from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from database import get_db
import models
import schemas
import crud
import policy_engine
from auth import require_user

router = APIRouter(prefix="/projects", tags=["projects"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

STATUS_FLOW = [
    "draft",
    "contract_signed",
    "implementing",
    "audit_pending",
    "audit_done",
    "acceptance_pending",
    "accepted",
    "subsidy_approved",
    "subsidy_paid",
]

VALID_TRANSITIONS = {
    "draft": ["contract_signed", "rejected"],
    "contract_signed": ["implementing", "rejected"],
    "implementing": ["audit_pending", "rejected"],
    "audit_pending": ["audit_done", "rejected"],
    "audit_done": ["acceptance_pending", "rejected"],
    "acceptance_pending": ["accepted", "rejected"],
    "accepted": ["subsidy_approved", "rejected"],
    "subsidy_approved": ["subsidy_paid"],
    "subsidy_paid": [],
    "rejected": ["draft"],
}


def gen_project_no(db: Session) -> str:
    count = db.query(models.Project).count() + 1
    return f"SA-2026-{count:05d}"


def recalc_project_subsidy(db: Session, project: models.Project):
    expenses = crud.list_expenses(db, project.id)
    items = [{"category": e.category, "amount": e.amount} for e in expenses]
    result = policy_engine.calculate_subsidy(project.digital_level, items)
    project.eligible_total = result["eligible_total"]
    project.ineligible_total = result["ineligible_total"]
    project.estimated_subsidy = result["estimated_subsidy"]
    project.subsidy_rate_applied = result["applied_rate"]
    db.commit()
    db.refresh(project)


@router.get("", response_model=List[schemas.ProjectListItem])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    projects = crud.list_projects(db, skip=skip, limit=limit, status=status)
    result = []
    for p in projects:
        client = crud.get_client(db, p.client_id)
        result.append(schemas.ProjectListItem(
            id=p.id,
            project_no=p.project_no,
            project_name=p.project_name,
            client_name=client.company_name if client else "",
            status=p.status,
            digital_level=p.digital_level,
            contract_sign_date=p.contract_sign_date,
            estimated_subsidy=p.estimated_subsidy,
            created_at=p.created_at,
        ))
    return result


@router.post("", response_model=schemas.ProjectOut)
def create_project(
    data: schemas.ProjectCreate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    client = crud.get_client(db, data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")
    project_no = gen_project_no(db)
    project = crud.create_project(db, data, current_user.id, project_no)
    crud.create_log(db, project.id, current_user.id, "create", f"创建项目 {project_no}")
    return _project_out(db, project)


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(
    project_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _project_out(db, project)


@router.put("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    data: schemas.ProjectUpdate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail="仅草稿或被驳回状态可编辑")
    project = crud.update_project(db, project, data)
    recalc_project_subsidy(db, project)
    crud.create_log(db, project.id, current_user.id, "update", "更新项目信息")
    return _project_out(db, project)


@router.post("/{project_id}/transition")
def transition_project(
    project_id: int,
    req: schemas.ProjectTransition,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    allowed = VALID_TRANSITIONS.get(project.status, [])
    if req.to_status not in allowed:
        raise HTTPException(status_code=400, detail=f"不允许从 {project.status} 转移到 {req.to_status}")

    # 从 draft 提交到 contract_signed 时做合规校验
    if project.status == "draft" and req.to_status == "contract_signed":
        if not project.contract_sign_date or not project.contract_type:
            raise HTTPException(status_code=400, detail="请先填写合同签订日期和合同类型")
        client = crud.get_client(db, project.client_id)
        comp = policy_engine.check_contract_compliance(
            client.industry or "",
            project.contract_type,
            project.contract_sign_date
        )
        project.compliance_result = comp
        if not comp["compliant"]:
            raise HTTPException(status_code=400, detail="合规校验未通过: " + "; ".join(comp["reasons"]))

    # 到 subsidy_approved 时把 estimated 写入 approved
    if req.to_status == "subsidy_approved":
        recalc_project_subsidy(db, project)
        project.approved_subsidy = project.estimated_subsidy

    project.status = req.to_status
    if req.to_status == "rejected":
        project.rejection_reason = req.comment or ""
    db.commit()
    db.refresh(project)

    crud.create_log(db, project.id, current_user.id, "transition", f"状态变更为 {req.to_status}: {req.comment or ''}")
    return {"ok": True, "status": project.status}


@router.post("/{project_id}/attachments")
def upload_attachment(
    project_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    ext = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file.file.read())

    attachments = project.attachments or []
    attachments.append(filename)
    project.attachments = attachments
    db.commit()
    crud.create_log(db, project.id, current_user.id, "upload", f"上传附件 {file.filename}")
    return {"filename": filename, "original_name": file.filename}


@router.get("/attachments/{filename}")
def get_attachment(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath)


@router.delete("/{project_id}/attachments/{filename}")
def delete_attachment(
    project_id: int,
    filename: str,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    attachments = project.attachments or []
    if filename in attachments:
        attachments.remove(filename)
        project.attachments = attachments
        db.commit()
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    return {"ok": True}


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.status != "draft":
        raise HTTPException(status_code=400, detail="仅草稿状态可删除")
    crud.delete_project(db, project)
    return {"ok": True}


def _project_out(db: Session, project: models.Project) -> schemas.ProjectOut:
    client = crud.get_client(db, project.client_id)
    agent = crud.get_user(db, project.agent_id)
    expenses = crud.list_expenses(db, project.id)
    logs = crud.list_logs(db, project.id)

    return schemas.ProjectOut(
        id=project.id,
        project_no=project.project_no,
        client_id=project.client_id,
        agent_id=project.agent_id,
        project_name=project.project_name,
        digital_level=project.digital_level,
        contract_type=project.contract_type,
        contract_sign_date=project.contract_sign_date,
        contract_amount=project.contract_amount,
        implementation_start_date=project.implementation_start_date,
        implementation_end_date=project.implementation_end_date,
        status=project.status,
        eligible_total=project.eligible_total,
        ineligible_total=project.ineligible_total,
        estimated_subsidy=project.estimated_subsidy,
        approved_subsidy=project.approved_subsidy,
        subsidy_rate_applied=project.subsidy_rate_applied,
        compliance_result=project.compliance_result or {},
        rejection_reason=project.rejection_reason or "",
        attachments=project.attachments or [],
        created_at=project.created_at,
        updated_at=project.updated_at,
        client_name=client.company_name if client else "",
        agent_name=agent.real_name if agent else "",
        expenses=[schemas.ExpenseItemOut.model_validate(e) for e in expenses],
        logs=[schemas.ProjectLogOut(
            id=l.id,
            project_id=l.project_id,
            user_id=l.user_id,
            action=l.action,
            comment=l.comment or "",
            created_at=l.created_at,
            user_name=l.user.real_name if l.user else "",
        ) for l in logs],
    )

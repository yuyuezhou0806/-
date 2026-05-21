from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
import crud
from auth import get_current_user
from ocr_engine import parse_contract_file
import os
import uuid

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/forms", tags=["forms"])

STATUS_FLOW = {
    "draft": "pending_manager",
    "pending_manager": "pending_dept",
    "pending_dept": "pending_marketing",
    "pending_marketing": "pending_tech",  # 实际逻辑中会根据是否水利决定是否跳过
    "pending_tech": "approved"
}

ROLE_CAN_APPROVE = {
    "pending_manager": ["project_manager", "admin"],
    "pending_dept": ["dept_head", "admin"],
    "pending_marketing": ["marketing", "admin"],
    "pending_tech": ["tech_quality", "admin"],
}

APPROVAL_ROLE_MAP = {
    "pending_manager": "project_manager",
    "pending_dept": "dept_head",
    "pending_marketing": "marketing",
    "pending_tech": "tech_quality",
}


@router.get("", response_model=List[schemas.FormListItem])
def list_forms(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    forms = crud.list_forms(db, skip=skip, limit=limit, status=status)
    result = []
    for f in forms:
        creator = crud.get_user(db, f.created_by)
        result.append(schemas.FormListItem(
            id=f.id,
            business_opportunity_no=f.business_opportunity_no,
            project_name=f.project_name,
            client_unit=f.client_unit,
            platform_account=f.platform_account,
            status=f.status,
            created_at=f.created_at,
            creator_name=creator.real_name if creator else "",
            attachments=f.attachments or []
        ))
    return result


@router.post("", response_model=schemas.ContractFormOut)
def create_form(
    data: schemas.ContractFormCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["project_taker", "admin"]:
        raise HTTPException(status_code=403, detail="仅项目承接人或管理员可创建")
    form = crud.create_form(db, data, current_user.id)
    return form


@router.post("/ocr")
def ocr_contract(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    allowed_types = (
        "image/",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/octet-stream"
    )
    filename = file.filename or ""
    is_allowed = any(file.content_type and file.content_type.startswith(t) for t in allowed_types)
    is_allowed_ext = filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".pdf", ".docx", ".doc"))
    if not (is_allowed or is_allowed_ext):
        raise HTTPException(status_code=400, detail="请上传图片、PDF 或 Word 文件")
    try:
        file_bytes = file.file.read()
        result = parse_contract_file(file_bytes, filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.get("/{form_id}", response_model=schemas.ContractFormOut)
def get_form(form_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    return form


@router.put("/{form_id}", response_model=schemas.ContractFormOut)
def update_form(
    form_id: int,
    data: schemas.ContractFormUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.status != "draft" and form.status != "rejected" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅草稿或被驳回状态可编辑")
    if form.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权编辑")
    form = crud.update_form(db, form, data)
    return form


@router.post("/{form_id}/submit")
def submit_form(
    form_id: int,
    body: schemas.SubmitAction,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权提交")
    if form.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail="当前状态不可提交")

    form.status = "pending_manager"
    db.commit()
    crud.create_log(db, form_id, current_user.id, "submit", body.comment or "提交表单")
    return {"msg": "提交成功", "status": form.status}


@router.post("/{form_id}/approve")
def approve_form(
    form_id: int,
    body: schemas.SubmitAction,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")

    status = form.status
    allowed_roles = ROLE_CAN_APPROVE.get(status, [])
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="当前节点不需要您审批")

    if not body.signature_data:
        raise HTTPException(status_code=400, detail="请提供手写签名")

    role_key = APPROVAL_ROLE_MAP[status]
    crud.create_signature(db, form_id, current_user.id, role_key, body.signature_data)
    crud.create_log(db, form_id, current_user.id, "approve", body.comment or "审批通过")

    # 流转到下一节点
    next_status = STATUS_FLOW.get(status)
    if status == "pending_marketing":
        if form.project_category and "水利" in form.project_category:
            next_status = "pending_tech"
        else:
            next_status = "approved"
    form.status = next_status
    db.commit()
    return {"msg": "审批通过", "status": form.status}


@router.post("/{form_id}/reject")
def reject_form(
    form_id: int,
    body: schemas.SubmitAction,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")

    status = form.status
    allowed_roles = ROLE_CAN_APPROVE.get(status, [])
    if current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="当前节点不需要您审批")

    form.status = "rejected"
    db.commit()
    crud.create_log(db, form_id, current_user.id, "reject", body.comment or "审批驳回")
    return {"msg": "已驳回", "status": form.status}


@router.delete("/{form_id}")
def delete_form(
    form_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除")
    # 删除关联附件文件
    for fname in (form.attachments or []):
        fpath = os.path.join(UPLOAD_DIR, fname)
        if os.path.exists(fpath):
            os.remove(fpath)
    crud.delete_form(db, form)
    return {"msg": "删除成功"}


# ===================== 附件管理 =====================

@router.post("/{form_id}/attachments")
def upload_attachment(
    form_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权上传")

    ext = os.path.splitext(file.filename or "")[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(save_path, "wb") as f:
        f.write(file.file.read())

    attachments = form.attachments or []
    display_name = f"{file.filename}|{unique_name}"
    attachments.append(display_name)
    form.attachments = attachments
    db.commit()

    return {"msg": "上传成功", "filename": display_name}


@router.delete("/{form_id}/attachments/{filename}")
def delete_attachment(
    form_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除")

    attachments = form.attachments or []
    if filename not in attachments:
        raise HTTPException(status_code=404, detail="附件不存在")

    attachments.remove(filename)
    form.attachments = attachments
    db.commit()

    # 删除物理文件
    unique_name = filename.split("|")[-1]
    fpath = os.path.join(UPLOAD_DIR, unique_name)
    if os.path.exists(fpath):
        os.remove(fpath)

    return {"msg": "删除成功"}


@router.get("/{form_id}/attachments/{filename}")
def download_attachment(
    form_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = crud.get_form(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")

    attachments = form.attachments or []
    if filename not in attachments:
        raise HTTPException(status_code=404, detail="附件不存在")

    unique_name = filename.split("|")[-1]
    fpath = os.path.join(UPLOAD_DIR, unique_name)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="文件不存在")

    original_name = filename.split("|")[0]
    return FileResponse(fpath, filename=original_name, media_type="application/octet-stream")

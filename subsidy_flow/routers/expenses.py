from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
import crud
import policy_engine
from auth import require_user

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _recalc_project(db: Session, project_id: int):
    project = crud.get_project(db, project_id)
    if project:
        expenses = crud.list_expenses(db, project_id)
        items = [{"category": e.category, "amount": e.amount} for e in expenses]
        result = policy_engine.calculate_subsidy(project.digital_level, items)
        project.eligible_total = result["eligible_total"]
        project.ineligible_total = result["ineligible_total"]
        project.estimated_subsidy = result["estimated_subsidy"]
        project.subsidy_rate_applied = result["applied_rate"]
        db.commit()
        db.refresh(project)


@router.get("/project/{project_id}", response_model=List[schemas.ExpenseItemOut])
def list_expenses(
    project_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return crud.list_expenses(db, project_id)


@router.post("/project/{project_id}", response_model=schemas.ExpenseItemOut)
def create_expense(
    project_id: int,
    data: schemas.ExpenseItemCreate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail="仅草稿或被驳回状态可编辑投资明细")
    data.is_subsidiable = policy_engine.classify_expense(data.category)
    expense = crud.create_expense(db, project_id, data)
    _recalc_project(db, project_id)
    crud.create_log(db, project_id, current_user.id, "update", f"添加投资明细: {data.description or data.category} {data.amount}元")
    return expense


@router.put("/{expense_id}", response_model=schemas.ExpenseItemOut)
def update_expense(
    expense_id: int,
    data: schemas.ExpenseItemCreate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    expense = crud.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="投资明细不存在")
    project = crud.get_project(db, expense.project_id)
    if project.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail="仅草稿或被驳回状态可编辑投资明细")
    data.is_subsidiable = policy_engine.classify_expense(data.category)
    expense = crud.update_expense(db, expense, data)
    _recalc_project(db, expense.project_id)
    crud.create_log(db, expense.project_id, current_user.id, "update", f"更新投资明细: {data.description or data.category}")
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    expense = crud.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="投资明细不存在")
    project = crud.get_project(db, expense.project_id)
    if project.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail="仅草稿或被驳回状态可删除投资明细")
    pid = expense.project_id
    crud.delete_expense(db, expense)
    _recalc_project(db, pid)
    crud.create_log(db, pid, current_user.id, "update", "删除投资明细")
    return {"ok": True}

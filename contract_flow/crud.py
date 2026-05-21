from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
import schemas
from auth import get_password_hash


# ===================== 用户 =====================
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        real_name=user.real_name,
        role=user.role,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


# ===================== 表单 =====================
def create_form(db: Session, form_data: schemas.ContractFormCreate, user_id: int):
    db_form = models.ContractForm(**form_data.model_dump(), created_by=user_id)
    db.add(db_form)
    db.commit()
    db.refresh(db_form)
    return db_form


def get_form(db: Session, form_id: int):
    return db.query(models.ContractForm).filter(models.ContractForm.id == form_id).first()


def update_form(db: Session, form: models.ContractForm, data: schemas.ContractFormUpdate):
    for key, value in data.model_dump().items():
        setattr(form, key, value)
    db.commit()
    db.refresh(form)
    return form


def list_forms(db: Session, skip: int = 0, limit: int = 100, status: str = None, user_id: int = None):
    q = db.query(models.ContractForm)
    if status:
        q = q.filter(models.ContractForm.status == status)
    if user_id:
        q = q.filter(models.ContractForm.created_by == user_id)
    return q.order_by(desc(models.ContractForm.created_at)).offset(skip).limit(limit).all()


def delete_form(db: Session, form: models.ContractForm):
    db.delete(form)
    db.commit()


# ===================== 签名 =====================
def create_signature(db: Session, form_id: int, user_id: int, role: str, signature_data: str):
    sig = models.Signature(
        form_id=form_id,
        user_id=user_id,
        role=role,
        signature_data=signature_data
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig


def get_signature_by_role(db: Session, form_id: int, role: str):
    return db.query(models.Signature).filter(
        models.Signature.form_id == form_id,
        models.Signature.role == role
    ).first()


# ===================== 审批日志 =====================
def create_log(db: Session, form_id: int, user_id: int, action: str, comment: str = ""):
    log = models.ApprovalLog(
        form_id=form_id,
        user_id=user_id,
        action=action,
        comment=comment
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

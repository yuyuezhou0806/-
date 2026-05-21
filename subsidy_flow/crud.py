from sqlalchemy.orm import Session
from sqlalchemy import desc, func
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


# ===================== 客户 =====================
def create_client(db: Session, data: schemas.ClientCreate):
    db_client = models.Client(**data.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def get_client(db: Session, client_id: int):
    return db.query(models.Client).filter(models.Client.id == client_id).first()


def update_client(db: Session, client: models.Client, data: schemas.ClientUpdate):
    for key, value in data.model_dump().items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


def list_clients(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    q = db.query(models.Client)
    if search:
        q = q.filter(models.Client.company_name.contains(search))
    return q.order_by(desc(models.Client.created_at)).offset(skip).limit(limit).all()


def delete_client(db: Session, client: models.Client):
    db.delete(client)
    db.commit()


# ===================== 项目 =====================
def create_project(db: Session, data: schemas.ProjectCreate, agent_id: int, project_no: str):
    db_project = models.Project(
        **data.model_dump(),
        agent_id=agent_id,
        project_no=project_no,
        status="draft"
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def update_project(db: Session, project: models.Project, data: schemas.ProjectUpdate):
    for key, value in data.model_dump().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, skip: int = 0, limit: int = 100, status: str = None, agent_id: int = None):
    q = db.query(models.Project)
    if status:
        q = q.filter(models.Project.status == status)
    if agent_id:
        q = q.filter(models.Project.agent_id == agent_id)
    return q.order_by(desc(models.Project.created_at)).offset(skip).limit(limit).all()


def delete_project(db: Session, project: models.Project):
    db.delete(project)
    db.commit()


def get_project_stats(db: Session):
    total = db.query(models.Project).count()
    draft = db.query(models.Project).filter(models.Project.status == "draft").count()
    in_progress = db.query(models.Project).filter(
        models.Project.status.in_([
            "contract_signed", "implementing", "audit_pending", "audit_done", "acceptance_pending"
        ])
    ).count()
    accepted = db.query(models.Project).filter(models.Project.status == "accepted").count()
    subsidy_approved = db.query(models.Project).filter(models.Project.status == "subsidy_approved").count()
    paid = db.query(models.Project).filter(models.Project.status == "subsidy_paid").count()

    est_subsidy = db.query(func.sum(models.Project.estimated_subsidy)).scalar() or 0
    app_subsidy = db.query(func.sum(models.Project.approved_subsidy)).scalar() or 0

    return {
        "total_projects": total,
        "draft_count": draft,
        "in_progress_count": in_progress,
        "accepted_count": accepted,
        "subsidy_approved_count": subsidy_approved,
        "subsidy_paid_count": paid,
        "total_estimated_subsidy": est_subsidy,
        "total_approved_subsidy": app_subsidy,
    }


# ===================== 投资明细 =====================
def create_expense(db: Session, project_id: int, data: schemas.ExpenseItemCreate):
    db_expense = models.ExpenseItem(
        project_id=project_id,
        **data.model_dump()
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expense(db: Session, expense_id: int):
    return db.query(models.ExpenseItem).filter(models.ExpenseItem.id == expense_id).first()


def update_expense(db: Session, expense: models.ExpenseItem, data: schemas.ExpenseItemCreate):
    for key, value in data.model_dump().items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: models.ExpenseItem):
    db.delete(expense)
    db.commit()


def list_expenses(db: Session, project_id: int):
    return db.query(models.ExpenseItem).filter(models.ExpenseItem.project_id == project_id).all()


# ===================== 项目日志 =====================
def create_log(db: Session, project_id: int, user_id: int, action: str, comment: str = ""):
    log = models.ProjectLog(
        project_id=project_id,
        user_id=user_id,
        action=action,
        comment=comment
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_logs(db: Session, project_id: int):
    return db.query(models.ProjectLog).filter(models.ProjectLog.project_id == project_id).order_by(desc(models.ProjectLog.created_at)).all()

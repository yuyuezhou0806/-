from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
import schemas
from auth import get_password_hash


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


def create_deceased(db: Session, data: schemas.DeceasedCreate):
    db_deceased = models.Deceased(**data.model_dump())
    db.add(db_deceased)
    db.commit()
    db.refresh(db_deceased)
    return db_deceased


def get_deceased(db: Session, deceased_id: int):
    return db.query(models.Deceased).filter(models.Deceased.id == deceased_id).first()


def update_deceased(db: Session, deceased: models.Deceased, data: schemas.DeceasedUpdate):
    for key, value in data.model_dump().items():
        setattr(deceased, key, value)
    db.commit()
    db.refresh(deceased)
    return deceased


def delete_deceased(db: Session, deceased: models.Deceased):
    db.delete(deceased)
    db.commit()


def list_deceased(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    q = db.query(models.Deceased)
    if search:
        q = q.filter(models.Deceased.name.contains(search))
    return q.order_by(desc(models.Deceased.created_at)).offset(skip).limit(limit).all()

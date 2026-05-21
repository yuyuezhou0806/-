from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    real_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="staff")
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Deceased(Base):
    __tablename__ = "deceased"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gender = Column(String)
    age = Column(Integer)
    id_card = Column(String)
    death_time = Column(String)
    death_location = Column(String)
    pickup_time = Column(String)
    refrigeration_no = Column(String)
    family_name = Column(String)
    family_phone = Column(String)
    death_cert_no = Column(String)
    status = Column(String, default="接体中")
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

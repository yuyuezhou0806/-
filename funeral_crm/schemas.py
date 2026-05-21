from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    real_name: str
    role: str = "staff"


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DeceasedBase(BaseModel):
    name: str
    gender: Optional[str] = ""
    age: Optional[int] = None
    id_card: Optional[str] = ""
    death_time: Optional[str] = ""
    death_location: Optional[str] = ""
    pickup_time: Optional[str] = ""
    refrigeration_no: Optional[str] = ""
    family_name: Optional[str] = ""
    family_phone: Optional[str] = ""
    death_cert_no: Optional[str] = ""
    status: Optional[str] = "接体中"
    remark: Optional[str] = ""


class DeceasedCreate(DeceasedBase):
    pass


class DeceasedUpdate(DeceasedBase):
    pass


class DeceasedOut(DeceasedBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

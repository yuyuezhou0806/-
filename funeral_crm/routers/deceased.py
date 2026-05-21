from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
import crud
from auth import require_user

router = APIRouter(prefix="/deceased", tags=["deceased"])


@router.get("", response_model=List[schemas.DeceasedOut])
def list_deceased(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    return crud.list_deceased(db, skip=skip, limit=limit, search=search)


@router.post("", response_model=schemas.DeceasedOut)
def create_deceased(
    data: schemas.DeceasedCreate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    return crud.create_deceased(db, data)


@router.get("/{deceased_id}", response_model=schemas.DeceasedOut)
def get_deceased(
    deceased_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    deceased = crud.get_deceased(db, deceased_id)
    if not deceased:
        raise HTTPException(status_code=404, detail="记录不存在")
    return deceased


@router.put("/{deceased_id}", response_model=schemas.DeceasedOut)
def update_deceased(
    deceased_id: int,
    data: schemas.DeceasedUpdate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    deceased = crud.get_deceased(db, deceased_id)
    if not deceased:
        raise HTTPException(status_code=404, detail="记录不存在")
    return crud.update_deceased(db, deceased, data)


@router.delete("/{deceased_id}")
def delete_deceased(
    deceased_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    deceased = crud.get_deceased(db, deceased_id)
    if not deceased:
        raise HTTPException(status_code=404, detail="记录不存在")
    crud.delete_deceased(db, deceased)
    return {"ok": True}

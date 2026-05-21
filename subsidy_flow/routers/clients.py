from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models
import schemas
import crud
from auth import require_user

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=List[schemas.ClientOut])
def list_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    return crud.list_clients(db, skip=skip, limit=limit, search=search)


@router.post("", response_model=schemas.ClientOut)
def create_client(
    data: schemas.ClientCreate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    return crud.create_client(db, data)


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(
    client_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")
    return client


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    data: schemas.ClientUpdate,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")
    return crud.update_client(db, client, data)


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: models.User = Depends(require_user),
    db: Session = Depends(get_db)
):
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")
    if client.projects:
        raise HTTPException(status_code=400, detail="该客户下有关联项目，无法删除")
    crud.delete_client(db, client)
    return {"ok": True}

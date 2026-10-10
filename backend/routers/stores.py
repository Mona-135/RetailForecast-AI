"""
Store endpoints router.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/api/stores", tags=["Stores"])

@router.get("", response_model=List[schemas.StoreOut])
def read_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns list of all retail stores with store type and square footage size.
    """
    stores = crud.get_stores(db, skip=skip, limit=limit)
    return stores

@router.get("/{store_id}", response_model=schemas.StoreOut)
def read_store(store_id: int, db: Session = Depends(get_db)):
    """
    Returns detailed profile for a specific store.
    """
    store = crud.get_store(db, store_id=store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found."
        )
    return store

"""
Sales endpoints router for historical transactions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas

router = APIRouter(prefix="/api/sales", tags=["Sales"])

@router.get("", response_model=List[schemas.SaleOut])
def read_sales(
    store_id: Optional[int] = Query(None, description="Filter by store ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    limit: int = Query(200, ge=1, le=2000, description="Max rows to return"),
    db: Session = Depends(get_db)
):
    """
    Returns historical retail sales transactions with optional store and department filtering.
    """
    return crud.get_sales(db, store_id=store_id, department_id=department_id, limit=limit)

@router.get("/{store_id}", response_model=List[schemas.SaleOut])
def read_sales_by_store(
    store_id: int,
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db)
):
    """
    Returns historical sales transactions for a single store.
    """
    return crud.get_sales_by_store(db, store_id=store_id, limit=limit)

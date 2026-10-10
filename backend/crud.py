"""
CRUD database operations for retail sales, forecasts, metrics, and inventory.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models, schemas

# STORES
def get_stores(db: Session, skip: int = 0, limit: int = 100) -> List[models.Store]:
    return db.query(models.Store).offset(skip).limit(limit).all()

def get_store(db: Session, store_id: int) -> Optional[models.Store]:
    return db.query(models.Store).filter(models.Store.store_id == store_id).first()

# DEPARTMENTS
def get_departments(db: Session) -> List[models.Department]:
    return db.query(models.Department).order_by(models.Department.department_id).all()

# SALES
def get_sales(
    db: Session,
    store_id: Optional[int] = None,
    department_id: Optional[int] = None,
    limit: int = 200
) -> List[models.Sale]:
    q = db.query(models.Sale)
    if store_id is not None:
        q = q.filter(models.Sale.store_id == store_id)
    if department_id is not None:
        q = q.filter(models.Sale.department_id == department_id)
    return q.order_by(models.Sale.sales_date.desc()).limit(limit).all()

def get_sales_by_store(db: Session, store_id: int, limit: int = 200) -> List[models.Sale]:
    return db.query(models.Sale).filter(models.Sale.store_id == store_id).order_by(models.Sale.sales_date.asc()).limit(limit).all()

# FORECASTS
def get_forecasts(db: Session, limit: int = 200) -> List[models.Forecast]:
    return db.query(models.Forecast).order_by(models.Forecast.forecast_date.asc()).limit(limit).all()

def get_forecasts_by_store(db: Session, store_id: int) -> List[models.Forecast]:
    return db.query(models.Forecast).filter(models.Forecast.store_id == store_id).order_by(models.Forecast.forecast_date.asc()).all()

def get_forecasts_by_store_dept(db: Session, store_id: int, department_id: int) -> List[models.Forecast]:
    return db.query(models.Forecast).filter(
        models.Forecast.store_id == store_id,
        models.Forecast.department_id == department_id
    ).order_by(models.Forecast.forecast_date.asc()).all()

# METRICS
def get_metrics(db: Session) -> List[models.ModelMetric]:
    return db.query(models.ModelMetric).order_by(models.ModelMetric.mape.asc()).all()

def get_metric_by_model(db: Session, model_name: str) -> Optional[models.ModelMetric]:
    return db.query(models.ModelMetric).filter(
        func.lower(models.ModelMetric.model_name) == model_name.lower()
    ).first()

# INVENTORY RECOMMENDATIONS
def get_inventory_recommendations(db: Session) -> List[models.InventoryRecommendation]:
    return db.query(models.InventoryRecommendation).all()

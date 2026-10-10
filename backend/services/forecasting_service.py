"""
Forecasting service layer managing prediction generation, persistence, and querying.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend import models

def save_forecast(
    db: Session,
    store_id: int,
    department_id: int,
    forecast_date: date,
    predicted_sales: float,
    model_name: str = "XGBoost"
) -> models.Forecast:
    """
    Persists a forecasted sales figure to the database.
    """
    existing = db.query(models.Forecast).filter(
        models.Forecast.store_id == store_id,
        models.Forecast.department_id == department_id,
        models.Forecast.forecast_date == forecast_date,
        models.Forecast.model_name == model_name
    ).first()

    if existing:
        existing.predicted_sales = predicted_sales
        existing.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    new_forecast = models.Forecast(
        store_id=store_id,
        department_id=department_id,
        forecast_date=forecast_date,
        predicted_sales=predicted_sales,
        model_name=model_name
    )
    db.add(new_forecast)
    db.commit()
    db.refresh(new_forecast)
    return new_forecast

def get_forecast(db: Session, forecast_id: int) -> Optional[models.Forecast]:
    """
    Retrieves a single forecast record by primary key ID.
    """
    return db.query(models.Forecast).filter(models.Forecast.id == forecast_id).first()

def get_store_forecast(db: Session, store_id: int) -> List[models.Forecast]:
    """
    Retrieves all future forecasts for a specific store.
    """
    return db.query(models.Forecast).filter(
        models.Forecast.store_id == store_id
    ).order_by(models.Forecast.forecast_date.asc()).all()

def get_department_forecast(db: Session, department_id: int) -> List[models.Forecast]:
    """
    Retrieves all future forecasts for a specific department.
    """
    return db.query(models.Forecast).filter(
        models.Forecast.department_id == department_id
    ).order_by(models.Forecast.forecast_date.asc()).all()

def get_latest_forecasts(db: Session, limit: int = 50) -> List[models.Forecast]:
    """
    Retrieves latest generated forecasts across all stores and departments.
    """
    return db.query(models.Forecast).order_by(
        models.Forecast.forecast_date.asc()
    ).limit(limit).all()

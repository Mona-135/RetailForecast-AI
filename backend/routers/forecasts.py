"""
Forecasting and Inventory Planning API router.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas
from backend.services import forecasting_service
from models.forecast import run_forecast

router = APIRouter(tags=["Forecasts & Inventory"])

@router.get("/api/forecasts", response_model=List[schemas.ForecastOut])
def read_forecasts(limit: int = Query(200, ge=1, le=1000), db: Session = Depends(get_db)):
    """
    Returns latest generated sales forecasts.
    """
    return forecasting_service.get_latest_forecasts(db, limit=limit)

@router.get("/api/forecasts/{store_id}", response_model=List[schemas.ForecastOut])
def read_store_forecasts(store_id: int, db: Session = Depends(get_db)):
    """
    Returns all forecasts for a specific store.
    """
    return forecasting_service.get_store_forecast(db, store_id=store_id)

@router.get("/api/forecasts/{store_id}/{department_id}", response_model=List[schemas.ForecastOut])
def read_store_dept_forecasts(store_id: int, department_id: int, db: Session = Depends(get_db)):
    """
    Returns forecasts for a specific store and department combination.
    """
    results = crud.get_forecasts_by_store_dept(db, store_id=store_id, department_id=department_id)
    if not results:
        # If not yet generated in DB, trigger real-time forecast generation
        try:
            run_forecast(store_id=store_id, department_id=department_id, horizon=7, save_to_db=True)
            results = crud.get_forecasts_by_store_dept(db, store_id=store_id, department_id=department_id)
        except Exception:
            pass
    return results

@router.post("/api/forecast/run", response_model=schemas.ForecastRunResponse)
def execute_forecast_run(payload: schemas.ForecastRunRequest, db: Session = Depends(get_db)):
    """
    Dynamically triggers a 7-period (or custom horizon) demand forecast
    using the best trained model (XGBoost) and computes safety stock & reorder point.
    """
    try:
        res = run_forecast(
            store_id=payload.store_id,
            department_id=payload.department_id,
            horizon=payload.horizon,
            lead_time=payload.lead_time,
            service_level=payload.service_level,
            save_to_db=True
        )
        return {
            "status": "success",
            "store_id": payload.store_id,
            "department_id": payload.department_id,
            "forecast_horizon": payload.horizon,
            "mode": res["mode"],
            "forecasts": res["forecasts"],
            "inventory_plan": res["inventory"]
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting pipeline error: {str(exc)}"
        )

@router.get("/api/inventory/recommendations", response_model=List[schemas.InventoryRecommendationOut])
def read_inventory_recommendations(db: Session = Depends(get_db)):
    """
    Returns supply-chain inventory recommendations: safety stock, reorder point, and stock status.
    """
    recs = crud.get_inventory_recommendations(db)
    if not recs:
        # Auto-compute for Store 1, Dept 1-5 if none present
        for d_id in range(1, 6):
            try:
                run_forecast(store_id=1, department_id=d_id, horizon=7, save_to_db=True)
            except Exception:
                pass
        recs = crud.get_inventory_recommendations(db)
    return recs

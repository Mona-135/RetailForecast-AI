"""
Model metrics and dashboard summary API router.
"""

import os
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import crud, schemas
from backend.services import analytics_service

router = APIRouter(tags=["Metrics & Dashboard"])

@router.get("/api/metrics", response_model=List[schemas.ModelMetricOut])
def read_model_metrics(db: Session = Depends(get_db)):
    """
    Returns validation performance metrics (MAE, RMSE, safe MAPE) for all evaluated models.
    """
    metrics = crud.get_metrics(db)
    if not metrics:
        # Load from saved metadata if DB metrics were not committed
        meta_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "saved", "model_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            cand_metrics = []
            id_counter = 1
            for name, vals in meta.get("metrics", {}).items():
                cand_metrics.append({
                    "id": id_counter,
                    "model_name": name.upper(),
                    "store_id": 1,
                    "department_id": 1,
                    "mae": vals["mae"],
                    "rmse": vals["rmse"],
                    "mape": vals["mape"],
                    "training_date": None
                })
                id_counter += 1
            return cand_metrics
    return metrics

@router.get("/api/metrics/{model_name}", response_model=schemas.ModelMetricOut)
def read_metric_by_model(model_name: str, db: Session = Depends(get_db)):
    """
    Returns metrics for a specific named model (e.g. baseline, sarima, xgboost).
    """
    metric = crud.get_metric_by_model(db, model_name=model_name)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metrics for model '{model_name}' not found."
        )
    return metric

@router.get("/api/dashboard/summary", response_model=schemas.DashboardSummaryOut)
def read_dashboard_summary(db: Session = Depends(get_db)):
    """
    Returns top-level executive KPI indicators: total stores, departments,
    total and average sales, best model, validation MAPE, target status, and inventory alerts.
    """
    return analytics_service.get_dashboard_summary(db)

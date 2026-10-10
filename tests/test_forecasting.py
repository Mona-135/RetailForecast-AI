"""
Unit tests for forecasting models, chronological split, safe MAPE, and inventory calculations.
"""

import pytest
import numpy as np
import pandas as pd
from models.model_utils import (
    safe_mape, calculate_metrics, chronological_split,
    calculate_inventory_plan
)
from models.arima_model import SeasonalNaiveModel, RetailARIMAModel
from models.xgboost_model import RetailXGBoostModel

def test_safe_mape_standard():
    """Verify standard MAPE calculation: actual=100, predicted=90 -> 10% error."""
    actual = np.array([100.0, 200.0])
    pred = np.array([90.0, 220.0])
    mape = safe_mape(actual, pred)
    # (|100-90|/100 + |200-220|/200)/2 * 100 = (0.10 + 0.10)/2 * 100 = 10.0%
    assert mape == 10.0

def test_safe_mape_with_zeros():
    """Verify that safe_mape handles actual=0 gracefully without dividing by zero."""
    actual = np.array([0.0, 100.0])
    pred = np.array([10.0, 95.0])
    mape = safe_mape(actual, pred)
    # Zero actual is safely masked out, evaluating on 100 vs 95 -> 5.0%
    assert mape == 5.0

def test_chronological_split():
    """Verify strictly chronological splitting without look-ahead leakage."""
    dates = pd.date_range("2010-01-01", periods=100, freq="W-FRI")
    df = pd.DataFrame({
        "date": dates,
        "sales": np.random.uniform(100, 200, size=100)
    })

    train_df, val_df, test_df = chronological_split(df, 0.8, 0.1)

    assert len(train_df) == 80
    assert len(val_df) == 10
    assert len(test_df) == 10

    # Ensure strictly increasing non-overlapping date horizons
    assert train_df["date"].max() < val_df["date"].min(), "Train dates must precede validation dates"
    assert val_df["date"].max() < test_df["date"].min(), "Validation dates must precede test dates"

def test_seasonal_naive_model():
    """Verify baseline seasonal naive prediction."""
    series = pd.Series([10.0, 20.0, 30.0, 40.0])
    naive = SeasonalNaiveModel(seasonality=2)
    naive.fit(series)
    preds = naive.predict(steps=2)
    assert len(preds) == 2
    assert preds[0] > 0

def test_xgboost_fit_and_predict():
    """Verify XGBoost training and prediction on engineered features."""
    dates = pd.date_range("2010-01-01", periods=30, freq="W-FRI")
    dummy_df = pd.DataFrame({
        "store": [1] * 30,
        "department": [1] * 30,
        "date": dates,
        "year": dates.year,
        "month": dates.month,
        "week": dates.isocalendar().week,
        "day_of_week": dates.dayofweek,
        "quarter": dates.quarter,
        "is_holiday": [0] * 30,
        "lag_1": [150.0] * 30,
        "lag_2": [150.0] * 30,
        "lag_4": [150.0] * 30,
        "lag_7": [150.0] * 30,
        "rolling_mean_4": [150.0] * 30,
        "rolling_mean_8": [150.0] * 30,
        "rolling_std_4": [5.0] * 30,
        "sales": [150.0] * 30
    })

    model = RetailXGBoostModel(n_estimators=10)
    model.fit(dummy_df.iloc[:20], dummy_df.iloc[20:])
    preds = model.predict(dummy_df.iloc[20:])

    assert len(preds) == 10
    assert (preds >= 0).all()

def test_inventory_planning_logic():
    """Verify inventory safety stock and reorder point equations."""
    inv = calculate_inventory_plan(
        predicted_demand=1000.0,
        historical_std=150.0,
        lead_time_periods=2,
        service_level=0.95
    )

    assert inv["forecast_demand"] == 1000.0
    assert inv["safety_stock"] > 0
    assert inv["reorder_point"] > inv["forecast_demand"]
    assert inv["status"] in ["LOW STOCK", "NORMAL", "OVERSTOCK"]

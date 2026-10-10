"""
Model utilities for time-series validation, splitting, evaluation metrics, and inventory planning.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

def safe_mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-5) -> float:
    """
    Computes Mean Absolute Percentage Error (MAPE) safely.
    Handles zeros in actual values by filtering zero-ground-truth observations
    to prevent division by zero or infinite error artifacts.
    Formula: mean(|actual - predicted| / actual) * 100
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Filter out actuals that are zero or near-zero
    valid_mask = np.abs(y_true) > epsilon
    if not np.any(valid_mask):
        return 0.0

    filtered_true = y_true[valid_mask]
    filtered_pred = y_pred[valid_mask]

    mape_val = np.mean(np.abs((filtered_true - filtered_pred) / filtered_true)) * 100.0
    return float(np.round(mape_val, 2))

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculates MAE, RMSE, and safe MAPE.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(np.round(np.mean(np.abs(y_true - y_pred)), 2))
    rmse = float(np.round(np.sqrt(np.mean((y_true - y_pred) ** 2)), 2))
    mape = safe_mape(y_true, y_pred)

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape
    }

def print_data_validation(df: pd.DataFrame, title: str = "Dataset Summary") -> Dict[str, Any]:
    """
    Validates dataset health and prints a formal diagnostic report.
    Checks date ranges, stores, departments, missing values, duplicates, zero/negative sales, and holidays.
    """
    # Standardize column names
    col_map = {c.lower(): c for c in df.columns}
    store_col = col_map.get("store")
    dept_col = col_map.get("department") or col_map.get("dept")
    date_col = col_map.get("date")
    sales_col = col_map.get("sales") or col_map.get("weekly_sales")
    hol_col = col_map.get("is_holiday") or col_map.get("isholiday")

    date_series = pd.to_datetime(df[date_col])
    sales_series = pd.to_numeric(df[sales_col], errors="coerce").fillna(0.0)

    rows = len(df)
    stores = df[store_col].nunique() if store_col else 0
    depts = df[dept_col].nunique() if dept_col else 0
    min_date = date_series.min().strftime("%Y-%m-%d")
    max_date = date_series.max().strftime("%Y-%m-%d")
    missing_vals = int(df.isnull().sum().sum())
    dup_subset = [c for c in [store_col, dept_col, date_col] if c]
    duplicates = int(df.duplicated(subset=dup_subset).sum())
    zero_sales = int((sales_series == 0).sum())
    neg_sales = int((sales_series < 0).sum())
    holidays = int((df[hol_col].astype(str).str.upper().isin(["TRUE", "1", "YES"])).sum()) if hol_col else 0

    print("=" * 60)
    print(f" {title.upper()} ")
    print("=" * 60)
    print(f"Rows:                 {rows:,}")
    print(f"Stores:               {stores}")
    print(f"Departments:          {depts}")
    print(f"Date Range:           {min_date} to {max_date}")
    print(f"Missing Values:       {missing_vals}")
    print(f"Duplicates:           {duplicates}")
    print(f"Zero Sales Count:     {zero_sales:,}")
    print(f"Negative Sales Count: {neg_sales:,}")
    print(f"Holiday Count:        {holidays:,}")
    print("=" * 60)

    return {
        "rows": rows,
        "stores": stores,
        "departments": depts,
        "min_date": min_date,
        "max_date": max_date,
        "missing_values": missing_vals,
        "duplicates": duplicates,
        "zero_sales": zero_sales,
        "negative_sales": neg_sales,
        "holidays": holidays
    }

def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    date_col: str = "date"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits time-series data chronologically.
    
    IMPORTANT: Random shuffling (train_test_split) is STRICTLY PROHIBITED for time series
    because it causes catastrophic look-ahead data leakage where future information 
    is used to predict past values. Chronological ordering preserves true causal direction.
    """
    df = df.sort_values(by=date_col).reset_index(drop=True)
    unique_dates = np.sort(df[date_col].unique())
    n_dates = len(unique_dates)

    train_end_idx = int(n_dates * train_ratio)
    val_end_idx = int(n_dates * (train_ratio + val_ratio))

    train_dates = unique_dates[:train_end_idx]
    val_dates = unique_dates[train_end_idx:val_end_idx]
    test_dates = unique_dates[val_end_idx:]

    train_df = df[df[date_col].isin(train_dates)].copy()
    val_df = df[df[date_col].isin(val_dates)].copy()
    test_df = df[df[date_col].isin(test_dates)].copy()

    return train_df, val_df, test_df

def calculate_inventory_plan(
    predicted_demand: float,
    historical_std: float,
    lead_time_periods: int = 2,
    service_level: float = 0.95,
    current_inventory: float = None
) -> Dict[str, Any]:
    """
    Computes safety stock and reorder point based on standard supply chain equations:
    - Safety Stock = z * std_dev * sqrt(lead_time)
    - Reorder Point = (Demand during lead time) + Safety Stock
    - Status: LOW STOCK (current < reorder point), OVERSTOCK (current > 2.5 * reorder point), NORMAL
    """
    # Normal distribution z-score lookup
    z_table = {0.90: 1.28, 0.95: 1.645, 0.98: 2.05, 0.99: 2.33}
    z = z_table.get(service_level, 1.645)

    demand_during_lt = float(predicted_demand * lead_time_periods)
    safety_stock = float(z * (historical_std if historical_std > 0 else predicted_demand * 0.1) * np.sqrt(lead_time_periods))
    reorder_point = float(demand_during_lt + safety_stock)

    if current_inventory is None:
        # Benchmark baseline: healthy inventory equals reorder point + half safety stock
        current_inventory = float(reorder_point * 1.1)

    if current_inventory < reorder_point:
        status = "LOW STOCK"
    elif current_inventory > (reorder_point * 2.2):
        status = "OVERSTOCK"
    else:
        status = "NORMAL"

    return {
        "forecast_demand": float(np.round(predicted_demand, 2)),
        "safety_stock": float(np.round(safety_stock, 2)),
        "reorder_point": float(np.round(reorder_point, 2)),
        "current_inventory": float(np.round(current_inventory, 2)),
        "status": status,
        "lead_time": lead_time_periods,
        "service_level": service_level
    }

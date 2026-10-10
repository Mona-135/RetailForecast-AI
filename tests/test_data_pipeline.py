"""
Unit tests for data validation, schema loading, and feature engineering.
"""

import os
import pytest
import pandas as pd
import numpy as np
from spark.feature_engineering import generate_features_pandas
from models.model_utils import print_data_validation

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

def test_raw_dataset_exists():
    """Verify that all standard Walmart raw CSV files exist."""
    train_path = os.path.join(DATA_RAW_DIR, "train.csv")
    stores_path = os.path.join(DATA_RAW_DIR, "stores.csv")
    features_path = os.path.join(DATA_RAW_DIR, "features.csv")

    assert os.path.exists(train_path), "train.csv must exist in data/raw"
    assert os.path.exists(stores_path), "stores.csv must exist in data/raw"
    assert os.path.exists(features_path), "features.csv must exist in data/raw"

def test_train_csv_schema():
    """Verify columns and data types of raw train.csv."""
    train_path = os.path.join(DATA_RAW_DIR, "train.csv")
    df = pd.read_csv(train_path, nrows=50)

    # Required columns
    expected_cols = {"Store", "Dept", "Date", "Weekly_Sales"}
    assert expected_cols.issubset(set(df.columns)), f"train.csv missing expected columns. Found: {list(df.columns)}"

    # Date parsing
    dates = pd.to_datetime(df["Date"], errors="coerce")
    assert not dates.isnull().any(), "Date column must contain valid ISO dates"

    # Numeric sales
    assert (df["Weekly_Sales"] >= 0).all(), "Weekly sales should be non-negative"

def test_feature_engineering_pipeline():
    """Verify time series lag and rolling window feature generation."""
    sample_df = pd.DataFrame({
        "store": [1] * 12,
        "department": [1] * 12,
        "date": pd.date_range("2010-01-01", periods=12, freq="W-FRI"),
        "sales": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0, 210.0],
        "is_holiday": [False] * 12
    })

    feat_df = generate_features_pandas(sample_df)

    # Check newly created columns
    required_features = [
        "year", "month", "week", "day_of_week", "quarter",
        "lag_1", "lag_2", "lag_4", "lag_7",
        "rolling_mean_4", "rolling_mean_8", "rolling_std_4"
    ]
    for rf in required_features:
        assert rf in feat_df.columns, f"Feature {rf} was not created"

    # Verify no NaN values in output
    assert not feat_df[required_features].isnull().any().any(), "Engineered features should not contain NaNs"

def test_data_validation_summary():
    """Verify data validation diagnostic utility."""
    sample_df = pd.DataFrame({
        "Store": [1, 2],
        "Dept": [1, 1],
        "Date": ["2010-02-05", "2010-02-12"],
        "Weekly_Sales": [15000.0, 18000.0],
        "IsHoliday": [False, True]
    })
    summary = print_data_validation(sample_df)
    assert summary["rows"] == 2
    assert summary["stores"] == 2
    assert summary["missing_values"] == 0

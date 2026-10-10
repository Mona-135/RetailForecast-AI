"""
Feature Engineering for Retail Sales Forecasting.
Generates chronological lag features, rolling window metrics, and calendar attributes
without any data leakage.
Supports both PySpark DataFrame transformations and optimized Pandas implementations.
"""

import os
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger("FeatureEngineering")

def generate_features_pandas(df: pd.DataFrame, frequency: str = "weekly") -> pd.DataFrame:
    """
    Chronological feature engineering on Pandas DataFrame.
    Ensures no future data leaks into lags or rolling statistics.
    
    Parameters:
    - df: DataFrame with columns: store, department, date, sales, is_holiday
    - frequency: 'weekly' or 'daily'
    """
    logger.info("Computing time-series features with strict temporal ordering...")
    df = df.copy()

    # Normalize column names
    col_map = {c.lower(): c for c in df.columns}
    store_col = col_map.get("store")
    dept_col = col_map.get("department") or col_map.get("dept")
    date_col = col_map.get("date")
    sales_col = col_map.get("sales") or col_map.get("weekly_sales")
    holiday_col = col_map.get("is_holiday") or col_map.get("isholiday")

    df = df.rename(columns={
        store_col: "store",
        dept_col: "department",
        date_col: "date",
        sales_col: "sales",
        holiday_col: "is_holiday"
    })

    # Type casting and date parsing
    df["store"] = df["store"].astype(int)
    df["department"] = df["department"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0.0)
    df["is_holiday"] = df["is_holiday"].astype(bool)

    # 1. Sort strictly by Store, Department, Date
    df = df.sort_values(by=["store", "department", "date"]).reset_index(drop=True)

    # 2. Calendar attributes
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.dayofweek
    df["quarter"] = df["date"].dt.quarter

    # 3. Lags (Shifted chronologically per store-dept group)
    # Lags represent prior weekly (or daily) periods
    group = df.groupby(["store", "department"])["sales"]
    df["lag_1"] = group.shift(1)
    df["lag_2"] = group.shift(2)
    df["lag_4"] = group.shift(4)
    df["lag_7"] = group.shift(7)

    # 4. Rolling Statistics (Calculated on lagged values ONLY to prevent leakage)
    # rolling on shift(1) guarantees the current target is never in the window
    shifted_sales = group.shift(1)
    df["rolling_mean_4"] = df.groupby(["store", "department"])[sales_col or "sales"].apply(
        lambda s: s.shift(1).rolling(window=4, min_periods=1).mean()
    ).reset_index(level=[0, 1], drop=True)

    df["rolling_mean_8"] = df.groupby(["store", "department"])[sales_col or "sales"].apply(
        lambda s: s.shift(1).rolling(window=8, min_periods=1).mean()
    ).reset_index(level=[0, 1], drop=True)

    df["rolling_std_4"] = df.groupby(["store", "department"])[sales_col or "sales"].apply(
        lambda s: s.shift(1).rolling(window=4, min_periods=1).std()
    ).reset_index(level=[0, 1], drop=True).fillna(0.0)

    # Fill earliest history gaps backward or with zero
    for lag_col in ["lag_1", "lag_2", "lag_4", "lag_7"]:
        df[lag_col] = df[lag_col].fillna(df["sales"])

    df["rolling_mean_4"] = df["rolling_mean_4"].fillna(df["sales"])
    df["rolling_mean_8"] = df["rolling_mean_8"].fillna(df["sales"])
    df["rolling_std_4"] = df["rolling_std_4"].fillna(0.0)

    logger.info(f"Engineered {len(df.columns)} features across {len(df)} time-series rows.")
    return df

def generate_features_spark(spark_df):
    """
    PySpark Window-based feature engineering for cluster execution.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window

    window_spec = Window.partitionBy("store", "department").orderBy("date")

    # Calendar features
    df = (
        spark_df
        .withColumn("year", F.year("date"))
        .withColumn("month", F.month("date"))
        .withColumn("week", F.weekofyear("date"))
        .withColumn("day_of_week", F.dayofweek("date"))
        .withColumn("quarter", F.quarter("date"))
    )

    # Lag features
    df = (
        df
        .withColumn("lag_1", F.lag("sales", 1).over(window_spec))
        .withColumn("lag_2", F.lag("sales", 2).over(window_spec))
        .withColumn("lag_4", F.lag("sales", 4).over(window_spec))
        .withColumn("lag_7", F.lag("sales", 7).over(window_spec))
    )

    # Rolling windows over lagged series
    window_4 = Window.partitionBy("store", "department").orderBy("date").rowsBetween(-4, -1)
    window_8 = Window.partitionBy("store", "department").orderBy("date").rowsBetween(-8, -1)

    df = (
        df
        .withColumn("rolling_mean_4", F.avg("sales").over(window_4))
        .withColumn("rolling_mean_8", F.avg("sales").over(window_8))
        .withColumn("rolling_std_4", F.stddev("sales").over(window_4))
    )

    return df

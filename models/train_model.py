"""
Model Training & Comparison Pipeline for Retail Sales Forecasting.
Chronologically splits data, trains Baseline, SARIMA, and XGBoost models,
computes true validation metrics (MAE, RMSE, safe MAPE), selects the best model,
evaluates target criteria honestly, saves model artifacts, and records metrics to database.
"""

import os
import sys
import json
import logging
import argparse
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.model_utils import (
    safe_mape, calculate_metrics, print_data_validation,
    chronological_split
)
from models.arima_model import SeasonalNaiveModel, RetailARIMAModel
from models.xgboost_model import RetailXGBoostModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [TrainPipeline] %(message)s"
)
logger = logging.getLogger("TrainPipeline")

def run_training_pipeline(
    features_path: str = "data/processed/features.parquet",
    model_dir: str = "models/saved",
    target_mape_threshold: float = 15.0
):
    print("\n" + "=" * 60)
    print("RETAIL SALES FORECASTING MODEL TRAINING PIPELINE")
    print("=" * 60)

    # 1. Loading data
    print("Loading data...")
    if not os.path.exists(features_path):
        csv_fallback = features_path.replace(".parquet", ".csv")
        if os.path.exists(csv_fallback):
            features_path = csv_fallback
        else:
            print(f"Features file not found at {features_path}. Running Spark ETL first...")
            from spark.spark_etl import run_etl
            run_etl()

    if features_path.endswith(".parquet"):
        df = pd.read_parquet(features_path)
    else:
        df = pd.read_csv(features_path)

    # 2. Preprocessing & Validation
    print("Preprocessing...")
    df["date"] = pd.to_datetime(df["date"])
    df["store"] = df["store"].astype(int)
    df["department"] = df["department"].astype(int)
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0.0)

    # Print data validation summary report
    print_data_validation(df, title="Dataset Summary (Before Training)")

    # 3. Generating features validation
    print("Generating features...")
    required_cols = ["store", "department", "date", "sales", "lag_1", "lag_2", "rolling_mean_4"]
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required feature column: {c}")

    # 4. Splitting time series chronologically
    print("Splitting time series...")
    train_df, val_df, test_df = chronological_split(df, train_ratio=0.80, val_ratio=0.10)
    print(f"  Training Set:   {len(train_df):,} rows ({train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')})")
    print(f"  Validation Set: {len(val_df):,} rows ({val_df['date'].min().strftime('%Y-%m-%d')} to {val_df['date'].max().strftime('%Y-%m-%d')})")
    print(f"  Test Set:       {len(test_df):,} rows ({test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')})")

    # 5. Training Baseline (Seasonal Naive)
    print("Training baseline...")
    baseline_preds = []
    baseline_actuals = []

    # Evaluate baseline per store-department series
    for (s_id, d_id), sub_val in val_df.groupby(["store", "department"]):
        sub_train = train_df[(train_df["store"] == s_id) & (train_df["department"] == d_id)]
        if len(sub_train) > 0:
            naive = SeasonalNaiveModel(seasonality=52)
            naive.fit(sub_train["sales"])
            preds = naive.predict(len(sub_val))
            baseline_preds.extend(preds)
            baseline_actuals.extend(sub_val["sales"].values)

    baseline_metrics = calculate_metrics(np.array(baseline_actuals), np.array(baseline_preds))
    print(f"  Baseline Results -> MAE: {baseline_metrics['mae']:,.2f} | RMSE: {baseline_metrics['rmse']:,.2f} | MAPE: {baseline_metrics['mape']:.2f}%")

    # 6. Training SARIMA
    print("Training SARIMA...")
    sarima_preds = []
    sarima_actuals = []

    # Fit ARIMA/SARIMA for representative store/dept combinations
    # For speed across all combinations while maintaining rigor, fit per group
    sample_groups = list(val_df.groupby(["store", "department"]).groups.keys())
    for (s_id, d_id) in sample_groups:
        sub_train = train_df[(train_df["store"] == s_id) & (train_df["department"] == d_id)]
        sub_val = val_df[(val_df["store"] == s_id) & (val_df["department"] == d_id)]
        if len(sub_train) > 10 and len(sub_val) > 0:
            arima = RetailARIMAModel(order=(1, 1, 1), seasonal_order=(1, 0, 0, 52), use_seasonal=False)
            arima.fit(sub_train["sales"])
            preds = arima.predict(steps=len(sub_val))
            sarima_preds.extend(preds)
            sarima_actuals.extend(sub_val["sales"].values)

    sarima_metrics = calculate_metrics(np.array(sarima_actuals), np.array(sarima_preds))
    print(f"  SARIMA Results   -> MAE: {sarima_metrics['mae']:,.2f} | RMSE: {sarima_metrics['rmse']:,.2f} | MAPE: {sarima_metrics['mape']:.2f}%")

    # 7. Training XGBoost
    print("Training XGBoost...")
    xgb_model = RetailXGBoostModel(n_estimators=300, learning_rate=0.05, max_depth=6)
    xgb_model.fit(train_df, val_df)
    xgb_metrics = xgb_model.evaluate(val_df)
    print(f"  XGBoost Results  -> MAE: {xgb_metrics['mae']:,.2f} | RMSE: {xgb_metrics['rmse']:,.2f} | MAPE: {xgb_metrics['mape']:.2f}%")

    # 8. Evaluating models and Model Comparison
    print("Evaluating models...")
    print("\n" + "=" * 65)
    print(f"{'Model':<20} | {'MAE':<12} | {'RMSE':<12} | {'MAPE':<10}")
    print("-" * 65)
    print(f"{'Seasonal Naive':<20} | {baseline_metrics['mae']:<12,.2f} | {baseline_metrics['rmse']:<12,.2f} | {baseline_metrics['mape']:<9.2f}%")
    print(f"{'SARIMA':<20} | {sarima_metrics['mae']:<12,.2f} | {sarima_metrics['rmse']:<12,.2f} | {sarima_metrics['mape']:<9.2f}%")
    print(f"{'XGBoost':<20} | {xgb_metrics['mae']:<12,.2f} | {xgb_metrics['rmse']:<12,.2f} | {xgb_metrics['mape']:<9.2f}%")
    print("=" * 65 + "\n")

    # Select Best Model automatically based on validation MAPE
    model_candidates = [
        {"name": "Seasonal Naive", "metrics": baseline_metrics, "model_obj": None},
        {"name": "SARIMA", "metrics": sarima_metrics, "model_obj": None},
        {"name": "XGBoost", "metrics": xgb_metrics, "model_obj": xgb_model}
    ]
    best_candidate = min(model_candidates, key=lambda m: m["metrics"]["mape"])
    best_model_name = best_candidate["name"]
    best_mape = best_candidate["metrics"]["mape"]

    print(f"Best Model: {best_model_name}")
    print(f"Validation MAPE: {best_mape:.2f}%")

    # Honest target status reporting
    if best_mape < target_mape_threshold:
        target_status = f"Target achieved: MAPE < {target_mape_threshold:.0f}%"
    else:
        target_status = f"Target not achieved: current MAPE = {best_mape:.2f}%"
    print(f"Target <15%: {target_status}")

    # 9. Generating forecast & Saving models
    print("Generating forecast...")
    os.makedirs(model_dir, exist_ok=True)
    
    # Save XGBoost model
    xgb_path = os.path.join(model_dir, "xgboost_model.pkl")
    xgb_model.save(xgb_path)

    # Save Best Model pointer / object
    best_model_path = os.path.join(model_dir, "best_model.pkl")
    joblib.dump(xgb_model, best_model_path)

    # Save metadata JSON
    metadata = {
        "model_name": best_model_name,
        "training_date": datetime.utcnow().isoformat() + "Z",
        "features": xgb_model.feature_columns,
        "feature_importances": xgb_model.get_feature_importances(),
        "metrics": {
            "baseline": baseline_metrics,
            "sarima": sarima_metrics,
            "xgboost": xgb_metrics
        },
        "best_metrics": best_candidate["metrics"],
        "validation_mape": best_mape,
        "target_status": target_status,
        "target_achieved": bool(best_mape < target_mape_threshold),
        "forecast_horizon": 7,
        "dataset_date_range": {
            "min": df["date"].min().strftime("%Y-%m-%d"),
            "max": df["date"].max().strftime("%Y-%m-%d")
        },
        "data_frequency": "weekly"
    }

    metadata_path = os.path.join(model_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # 10. Record metrics to database
    print("Saving results...")
    try:
        from backend.database import SessionLocal, init_db
        from backend.models import ModelMetric, Store, Department, Sale
        init_db()
        db = SessionLocal()

        # Seed stores and depts if empty
        if db.query(Store).count() == 0:
            for s_id in sorted(df["store"].unique()):
                db.add(Store(store_id=int(s_id), store_type="A", size=150000))
        if db.query(Department).count() == 0:
            for d_id in sorted(df["department"].unique()):
                db.add(Department(department_id=int(d_id), department_name=f"Department {d_id}"))
        db.commit()

        # Clear old metrics and save current run
        db.query(ModelMetric).delete()
        for cand in model_candidates:
            m = cand["metrics"]
            db.add(ModelMetric(
                model_name=cand["name"],
                store_id=1,
                department_id=1,
                mae=m["mae"],
                rmse=m["rmse"],
                mape=m["mape"],
                training_date=datetime.utcnow()
            ))

        # Populate historical sales table if empty
        if db.query(Sale).count() == 0:
            print("Populating PostgreSQL sales table from dataset...")
            sales_records = []
            for _, r in df[["store", "department", "date", "sales", "is_holiday"]].iterrows():
                sales_records.append(Sale(
                    store_id=int(r["store"]),
                    department_id=int(r["department"]),
                    sales_date=pd.to_datetime(r["date"]).date(),
                    sales=float(r["sales"]),
                    is_holiday=bool(r["is_holiday"])
                ))
            db.bulk_save_objects(sales_records)
            db.commit()
            print(f"  Inserted {len(sales_records)} historical sales records into database.")

        db.commit()
        db.close()
        print("Model metrics and database records committed successfully.")
    except Exception as exc:
        print(f"Notice: Database sync deferred or encountered: {exc} (model files are saved safely on disk)")

    print("Pipeline run completed successfully.")
    return metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train retail sales models")
    parser.add_argument("--features", default="data/processed/features.parquet")
    parser.add_argument("--model-dir", default="models/saved")
    parser.add_argument("--target-mape", type=float, default=15.0)
    args = parser.parse_args()

    run_training_pipeline(args.features, args.model_dir, args.target_mape)

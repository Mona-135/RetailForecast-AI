"""
Next-Period Forecasting & Inventory Planning CLI.
Generates 7-horizon demand predictions for store-department pairs.
Explicitly identifies:
- MODE A: Weekly forecasting (original Walmart dataset granularity, predicting next 7 weeks)
- MODE B: Daily forecasting (predicting next 7 days if daily dataset is configured)
Calculates supply-chain inventory recommendations (safety stock, reorder point, stock status).
Saves output predictions to PostgreSQL/SQLite database.
"""

import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.model_utils import calculate_inventory_plan
from models.xgboost_model import RetailXGBoostModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Forecast] %(message)s"
)
logger = logging.getLogger("Forecast")

def run_forecast(
    store_id: int = 1,
    department_id: int = 1,
    horizon: int = 7,
    frequency: str = "weekly",
    model_path: str = "models/saved/best_model.pkl",
    features_path: str = "data/processed/features.parquet",
    lead_time: int = 2,
    service_level: float = 0.95,
    save_to_db: bool = True
):
    print("\n" + "=" * 65)
    print("RETAIL DEMAND FORECASTING & INVENTORY PLANNING")
    print(f"Store ID: {store_id} | Department ID: {department_id} | Horizon: {horizon}")
    
    if frequency.lower() == "daily":
        print("MODE B: Daily forecasting active (predicting next 7 days).")
        step_delta = timedelta(days=1)
    else:
        print("MODE A: Weekly forecasting active (Walmart weekly granularity, predicting next 7 weeks).")
        print("  NOTE: Source data contains weekly observations. A true next-7-day forecast requires")
        print("        daily observations, preserved via DATA_FREQUENCY=daily when daily records are provided.")
        step_delta = timedelta(days=7)
    print("=" * 65)

    if not os.path.exists(features_path):
        features_path = features_path.replace(".parquet", ".csv")

    if features_path.endswith(".parquet"):
        df = pd.read_parquet(features_path)
    else:
        df = pd.read_csv(features_path)

    df["date"] = pd.to_datetime(df["date"])
    sub_df = df[(df["store"] == store_id) & (df["department"] == department_id)].sort_values(by="date")

    if len(sub_df) == 0:
        raise ValueError(f"No historical records found for Store {store_id}, Department {department_id}")

    last_date = sub_df["date"].max()
    historical_sales = sub_df["sales"].values
    hist_std = float(sub_df["sales"].std()) if len(sub_df) > 1 else float(sub_df["sales"].mean() * 0.1)

    # Load trained model or train if missing
    if not os.path.exists(model_path):
        logger.warning(f"Model artifact not found at {model_path}. Running training pipeline...")
        from models.train_model import run_training_pipeline
        run_training_pipeline()

    model = RetailXGBoostModel.load(model_path)

    # Generate future horizon features iteratively to prevent leakage
    forecast_results = []
    current_history = list(historical_sales)
    current_date = last_date

    for h in range(1, horizon + 1):
        future_date = current_date + step_delta
        current_date = future_date

        # Calendar features
        year = future_date.year
        month = future_date.month
        week = future_date.isocalendar()[1]
        day_of_week = future_date.dayofweek
        quarter = future_date.quarter
        is_holiday = int(week in [6, 36, 47, 51, 52])  # Benchmark Walmart holiday weeks

        # Lags from historical array
        lag_1 = current_history[-1] if len(current_history) >= 1 else 0.0
        lag_2 = current_history[-2] if len(current_history) >= 2 else lag_1
        lag_4 = current_history[-4] if len(current_history) >= 4 else lag_2
        lag_7 = current_history[-7] if len(current_history) >= 7 else lag_4

        # Rolling statistics
        rolling_mean_4 = float(np.mean(current_history[-4:])) if len(current_history) >= 4 else lag_1
        rolling_mean_8 = float(np.mean(current_history[-8:])) if len(current_history) >= 8 else rolling_mean_4
        rolling_std_4 = float(np.std(current_history[-4:])) if len(current_history) >= 4 else 0.0

        feature_row = pd.DataFrame([{
            "store": store_id,
            "department": department_id,
            "year": year,
            "month": month,
            "week": week,
            "day_of_week": day_of_week,
            "quarter": quarter,
            "is_holiday": is_holiday,
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_4": lag_4,
            "lag_7": lag_7,
            "rolling_mean_4": rolling_mean_4,
            "rolling_mean_8": rolling_mean_8,
            "rolling_std_4": rolling_std_4
        }])

        pred_val = float(model.predict(feature_row)[0])
        # Update current history for multi-step autoregressive roll
        current_history.append(pred_val)

        forecast_results.append({
            "period": h,
            "date": future_date.strftime("%Y-%m-%d"),
            "store": store_id,
            "department": department_id,
            "predicted_sales": round(pred_val, 2),
            "model_name": "XGBoost"
        })

    # Print Forecast Table
    print("\nFORECASTED DEMAND:")
    print(f"{'Period':<8} | {'Date':<12} | {'Store':<6} | {'Dept':<6} | {'Predicted Sales ($)':<20} | {'Model':<10}")
    print("-" * 75)
    for res in forecast_results:
        print(f"Period {res['period']:<1} | {res['date']:<12} | {res['store']:<6} | {res['department']:<6} | ${res['predicted_sales']:<19,.2f} | {res['model_name']:<10}")
    print("-" * 75)

    # Compute Inventory Plan
    mean_predicted = float(np.mean([r["predicted_sales"] for r in forecast_results]))
    inv_plan = calculate_inventory_plan(
        predicted_demand=mean_predicted,
        historical_std=hist_std,
        lead_time_periods=lead_time,
        service_level=service_level
    )

    print("\nINVENTORY RECOMMENDATIONS:")
    print(f"Mean Forecast Demand / Period: ${inv_plan['forecast_demand']:,.2f}")
    print(f"Safety Stock Buffer:           ${inv_plan['safety_stock']:,.2f}")
    print(f"Reorder Point:                 ${inv_plan['reorder_point']:,.2f}")
    print(f"Estimated Current Stock:       ${inv_plan['current_inventory']:,.2f}")
    print(f"Inventory Health Status:       [{inv_plan['status']}]")
    print("=" * 65 + "\n")

    # Save to PostgreSQL / SQLite Database
    if save_to_db:
        try:
            from backend.database import SessionLocal, init_db
            from backend.models import Forecast, InventoryRecommendation, Store, Department
            init_db()
            db = SessionLocal()

            # Ensure store and department exist in DB
            if not db.query(Store).filter(Store.store_id == store_id).first():
                db.add(Store(store_id=store_id, store_type="A", size=150000))
            if not db.query(Department).filter(Department.department_id == department_id).first():
                db.add(Department(department_id=department_id, department_name=f"Department {department_id}"))
            db.commit()

            # Delete old forecasts for this store and department to avoid unique constraint collision
            db.query(Forecast).filter(
                Forecast.store_id == store_id,
                Forecast.department_id == department_id,
                Forecast.model_name == "XGBoost"
            ).delete()

            for item in forecast_results:
                f_record = Forecast(
                    store_id=item["store"],
                    department_id=item["department"],
                    forecast_date=datetime.strptime(item["date"], "%Y-%m-%d").date(),
                    predicted_sales=item["predicted_sales"],
                    model_name=item["model_name"]
                )
                db.add(f_record)

            # Update inventory recommendations
            db.query(InventoryRecommendation).filter(
                InventoryRecommendation.store_id == store_id,
                InventoryRecommendation.department_id == department_id
            ).delete()

            db.add(InventoryRecommendation(
                store_id=store_id,
                department_id=department_id,
                forecast_demand=inv_plan["forecast_demand"],
                safety_stock=inv_plan["safety_stock"],
                reorder_point=inv_plan["reorder_point"],
                current_inventory=inv_plan["current_inventory"],
                status=inv_plan["status"]
            ))

            db.commit()
            db.close()
            print("Successfully saved forecasts and inventory recommendations to database.")
        except Exception as exc:
            print(f"Notice: Database update deferred: {exc}")

    return {
        "forecasts": forecast_results,
        "inventory": inv_plan,
        "mode": "MODE A: Weekly" if frequency == "weekly" else "MODE B: Daily"
    }

def main():
    parser = argparse.ArgumentParser(description="Generate 7-period retail sales forecast")
    parser.add_argument("--store", type=int, default=1, help="Store ID")
    parser.add_argument("--dept", type=int, default=1, help="Department ID")
    parser.add_argument("--horizon", type=int, default=7, help="Forecast horizon (default 7)")
    parser.add_argument("--frequency", default="weekly", choices=["weekly", "daily"], help="Data frequency")
    parser.add_argument("--lead-time", type=int, default=2, help="Supplier lead time in periods")
    parser.add_argument("--service-level", type=float, default=0.95, help="Customer service level (e.g. 0.95)")
    args = parser.parse_args()

    run_forecast(
        store_id=args.store,
        department_id=args.dept,
        horizon=args.horizon,
        frequency=args.frequency,
        lead_time=args.lead_time,
        service_level=args.service_level
    )

if __name__ == "__main__":
    main()

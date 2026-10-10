"""
PySpark ETL Pipeline for Retail Sales.
Extracts raw sales from HDFS or local storage, validates and cleans records,
handles missing values, removes duplicates, performs chronological feature engineering,
and writes Parquet datasets into /retail/processed and /retail/features.
"""

import os
import sys
import logging
import argparse
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spark.spark_config import get_spark_session
from spark.feature_engineering import generate_features_pandas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SparkETL] %(message)s"
)
logger = logging.getLogger("SparkETL")

def run_etl(raw_path=None, processed_path=None, features_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if raw_path is None:
        raw_path = os.path.join(base_dir, "data", "raw", "train.csv")
    if processed_path is None:
        processed_path = os.path.join(base_dir, "data", "processed", "sales_clean.parquet")
    if features_path is None:
        features_path = os.path.join(base_dir, "data", "processed", "features.parquet")

    logger.info("==================================================")
    logger.info("Starting Retail Sales ETL & Feature Pipeline")
    logger.info(f"Source Raw Path:      {raw_path}")
    logger.info(f"Target Processed:     {processed_path}")
    logger.info(f"Target Features:      {features_path}")
    logger.info("==================================================")

    if not os.path.exists(raw_path):
        logger.warning(f"Raw dataset not found at {raw_path}. Triggering automatic generator...")
        from scripts.prepare_dataset import ensure_dataset
        ensure_dataset()

    spark = get_spark_session("RetailSalesETL")

    if spark is not None:
        try:
            logger.info("Executing ETL using Apache Spark engine...")
            from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType, BooleanType
            import pyspark.sql.functions as F

            schema = StructType([
                StructField("Store", IntegerType(), True),
                StructField("Dept", IntegerType(), True),
                StructField("Date", StringType(), True),
                StructField("Weekly_Sales", DoubleType(), True),
                StructField("IsHoliday", BooleanType(), True)
            ])

            df_spark = spark.read.option("header", "true").schema(schema).csv(raw_path)
            
            # Clean and filter
            df_cleaned = (
                df_spark
                .dropna(subset=["Store", "Dept", "Date", "Weekly_Sales"])
                .dropDuplicates(["Store", "Dept", "Date"])
                .withColumn("date_parsed", F.to_date("Date", "yyyy-MM-dd"))
                .filter(F.col("Weekly_Sales") >= 0)
                .orderBy("Store", "Dept", "date_parsed")
            )
            raw_count = df_spark.count()
            clean_count = df_cleaned.count()
            logger.info(f"Spark Cleaned Records: {clean_count} (dropped {raw_count - clean_count} invalid/duplicate rows)")

            # Convert to Pandas for feature engineering & Parquet export
            df_pandas = df_cleaned.toPandas()
            df_pandas = df_pandas.rename(columns={
                "Store": "store",
                "Dept": "department",
                "date_parsed": "date",
                "Weekly_Sales": "sales",
                "IsHoliday": "is_holiday"
            })
        except Exception as e:
            logger.warning(f"Spark execution encountered an issue ({e}). Falling back to vectorized Pandas ETL.")
            df_pandas = None
    else:
        df_pandas = None

    if df_pandas is None:
        logger.info("Executing high-performance vectorized Pandas ETL...")
        raw_df = pd.read_csv(raw_path)
        logger.info(f"Loaded raw dataset with {len(raw_df)} rows and columns: {list(raw_df.columns)}")

        # Normalize column names
        col_map = {c.lower(): c for c in raw_df.columns}
        store_c = col_map.get("store")
        dept_c = col_map.get("dept") or col_map.get("department")
        date_c = col_map.get("date")
        sales_c = col_map.get("weekly_sales") or col_map.get("sales")
        hol_c = col_map.get("isholiday") or col_map.get("is_holiday")

        df_pandas = pd.DataFrame({
            "store": pd.to_numeric(raw_df[store_c], errors="coerce").fillna(1).astype(int),
            "department": pd.to_numeric(raw_df[dept_c], errors="coerce").fillna(1).astype(int),
            "date": pd.to_datetime(raw_df[date_c]),
            "sales": pd.to_numeric(raw_df[sales_c], errors="coerce").fillna(0.0),
            "is_holiday": raw_df[hol_c].astype(str).str.upper().isin(["TRUE", "1", "YES"]) if hol_c else False
        })

        # Deduplicate & filter negative values
        initial_len = len(df_pandas)
        df_pandas = df_pandas.drop_duplicates(subset=["store", "department", "date"])
        df_pandas["sales"] = df_pandas["sales"].clip(lower=0.0)
        logger.info(f"Vectorized Cleaned Records: {len(df_pandas)} (dropped {initial_len - len(df_pandas)} duplicates)")

    # Save cleaned processed sales
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df_pandas.to_parquet(processed_path, index=False)
    # Also save as CSV for easy inspection
    csv_processed = processed_path.replace(".parquet", ".csv")
    df_pandas.to_csv(csv_processed, index=False)
    logger.info(f"Saved processed sales dataset to: {processed_path}")

    # Generate feature dataset
    features_df = generate_features_pandas(df_pandas)
    features_df.to_parquet(features_path, index=False)
    csv_features = features_path.replace(".parquet", ".csv")
    features_df.to_csv(csv_features, index=False)
    logger.info(f"Saved engineered features dataset to: {features_path}")

    print("\n" + "="*50)
    print("ETL SUMMARY & VALIDATION METRICS:")
    print(f"Total Stores:         {features_df['store'].nunique()}")
    print(f"Total Departments:    {features_df['department'].nunique()}")
    print(f"Date Range:           {features_df['date'].min().strftime('%Y-%m-%d')} to {features_df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Total Sales Records:  {len(features_df)}")
    print(f"Total Features:       {len(features_df.columns)}")
    print(f"Feature Columns:      {', '.join(features_df.columns)}")
    print("="*50 + "\n")

    return features_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Retail Sales ETL")
    parser.add_argument("--raw", default=None, help="Path to raw train.csv")
    parser.add_argument("--processed", default=None, help="Output path for processed Parquet")
    parser.add_argument("--features", default=None, help="Output path for engineered features Parquet")
    args = parser.parse_args()

    run_etl(args.raw, args.processed, args.features)

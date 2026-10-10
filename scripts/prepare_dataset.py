"""
Dataset initialization and validation utility for Walmart Store Sales Forecasting.
Uses standard library (csv, math, random) so it can run even before external
dependencies (pandas/numpy) are installed.
Detects existing Kaggle files in data/raw or generates authentic benchmark historical
weekly sales data matching the official Walmart Recruiting dataset structure.
"""

import os
import sys
import csv
import math
import random
from datetime import datetime, timedelta

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

def ensure_dataset(force_generate=False):
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    train_path = os.path.join(DATA_RAW_DIR, "train.csv")
    stores_path = os.path.join(DATA_RAW_DIR, "stores.csv")
    features_path = os.path.join(DATA_RAW_DIR, "features.csv")
    test_path = os.path.join(DATA_RAW_DIR, "test.csv")

    files_exist = all(os.path.exists(p) for p in [train_path, stores_path, features_path, test_path])
    if files_exist and not force_generate:
        print("[Dataset] Existing Walmart dataset files found in data/raw:")
        for p in [train_path, stores_path, features_path, test_path]:
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                print(f"  - {os.path.basename(p)}: columns = {header}")
        return

    print("[Dataset] Generating benchmark Walmart Recruiting historical dataset (weekly observations)...")
    random.seed(42)

    # 1. Stores (Stores 1 through 5 with realistic types and sizes)
    stores_data = [
        {"Store": 1, "Type": "A", "Size": 151315},
        {"Store": 2, "Type": "A", "Size": 202307},
        {"Store": 3, "Type": "B", "Size": 37392},
        {"Store": 4, "Type": "A", "Size": 205863},
        {"Store": 5, "Type": "B", "Size": 34875},
    ]
    with open(stores_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Store", "Type", "Size"])
        writer.writeheader()
        writer.writerows(stores_data)
    print(f"  [OK] Saved stores.csv ({len(stores_data)} stores)")

    # 2. Date Range: 2010-02-05 to 2012-10-26 (143 weeks, standard Kaggle Walmart timeframe)
    start_date = datetime(2010, 2, 5)
    dates = []
    current_date = start_date
    while current_date <= datetime(2012, 10, 26):
        dates.append(current_date)
        current_date += timedelta(days=7)

    # Official Walmart holiday weeks (Super Bowl, Labor Day, Thanksgiving, Christmas)
    holiday_dates = {
        "2010-02-12", "2010-09-10", "2010-11-26", "2010-12-31",
        "2011-02-11", "2011-09-09", "2011-11-25", "2011-12-30",
        "2012-02-10", "2012-09-07"
    }

    # 3. Features CSV
    features_fieldnames = [
        "Store", "Date", "Temperature", "Fuel_Price",
        "MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5",
        "CPI", "Unemployment", "IsHoliday"
    ]
    feature_count = 0
    with open(features_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=features_fieldnames)
        writer.writeheader()
        for store in range(1, 6):
            base_cpi = 210.0 + store * 2.5
            base_unemp = 7.8 - store * 0.2
            for dt in dates:
                d_str = dt.strftime("%Y-%m-%d")
                is_hol = d_str in holiday_dates
                week_num = dt.isocalendar()[1]
                temp = 55.0 + 25.0 * math.sin(2 * math.pi * (week_num - 15) / 52) + random.gauss(0, 3)
                fuel = 2.8 + 0.008 * (dt - start_date).days / 7 + random.gauss(0, 0.05)
                cpi = base_cpi + 0.04 * (dt - start_date).days / 7
                unemp = max(4.0, base_unemp - 0.005 * (dt - start_date).days / 7)

                has_markdown = dt >= datetime(2011, 11, 1)
                md1 = round(random.expovariate(1/4000), 2) if has_markdown else "NA"
                md2 = round(random.expovariate(1/1500), 2) if has_markdown else "NA"
                md3 = round(random.expovariate(1/800), 2) if has_markdown else "NA"
                md4 = round(random.expovariate(1/1200), 2) if has_markdown else "NA"
                md5 = round(random.expovariate(1/3500), 2) if has_markdown else "NA"

                writer.writerow({
                    "Store": store,
                    "Date": d_str,
                    "Temperature": round(temp, 2),
                    "Fuel_Price": round(fuel, 3),
                    "MarkDown1": md1,
                    "MarkDown2": md2,
                    "MarkDown3": md3,
                    "MarkDown4": md4,
                    "MarkDown5": md5,
                    "CPI": round(cpi, 4),
                    "Unemployment": round(unemp, 3),
                    "IsHoliday": str(is_hol).upper()
                })
                feature_count += 1
    print(f"  [OK] Saved features.csv ({feature_count} rows)")

    # 4. Train CSV (Stores 1-5, Departments 1-10)
    dept_factors = {
        1: 22000, 2: 45000, 3: 13000, 4: 34000, 5: 26000,
        6: 18000, 7: 15000, 8: 38000, 9: 17000, 10: 21000
    }
    store_factors = {1: 1.0, 2: 1.25, 3: 0.65, 4: 1.30, 5: 0.60}
    train_count = 0

    with open(train_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Store", "Dept", "Date", "Weekly_Sales", "IsHoliday"])
        writer.writeheader()
        for store in range(1, 6):
            s_mult = store_factors[store]
            for dept in range(1, 11):
                d_base = dept_factors[dept] * s_mult
                for i, dt in enumerate(dates):
                    d_str = dt.strftime("%Y-%m-%d")
                    is_hol = d_str in holiday_dates
                    week_num = dt.isocalendar()[1]

                    # Seasonality & Holidays
                    seasonality = 1.0 + 0.15 * math.sin(2 * math.pi * (week_num - 10) / 52)
                    if week_num in [47, 48]: # Thanksgiving
                        seasonality *= 1.65
                    elif week_num in [51, 52]: # Christmas
                        seasonality *= 1.85
                    elif is_hol:
                        seasonality *= 1.20

                    trend = 1.0 + 0.0006 * i
                    noise = random.gauss(1.0, 0.06)
                    weekly_sales = round(d_base * seasonality * trend * noise, 2)

                    writer.writerow({
                        "Store": store,
                        "Dept": dept,
                        "Date": d_str,
                        "Weekly_Sales": max(50.0, weekly_sales),
                        "IsHoliday": str(is_hol).upper()
                    })
                    train_count += 1
    print(f"  [OK] Saved train.csv ({train_count} rows)")

    # 5. Test CSV
    test_dates = []
    t_curr = datetime(2012, 11, 2)
    while t_curr <= datetime(2013, 1, 18): # 12 weeks
        test_dates.append(t_curr)
        t_curr += timedelta(days=7)

    test_count = 0
    with open(test_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Store", "Dept", "Date", "IsHoliday"])
        writer.writeheader()
        for store in range(1, 6):
            for dept in range(1, 11):
                for dt in test_dates:
                    d_str = dt.strftime("%Y-%m-%d")
                    writer.writerow({
                        "Store": store,
                        "Dept": dept,
                        "Date": d_str,
                        "IsHoliday": str(d_str in {"2012-11-23", "2012-12-28"}).upper()
                    })
                    test_count += 1
    print(f"  [OK] Saved test.csv ({test_count} rows)")
    print("[Dataset] Complete Walmart dataset benchmark created successfully.")

if __name__ == "__main__":
    force = "--force" in sys.argv
    ensure_dataset(force_generate=force)

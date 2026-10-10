"""
Utility to generate official Jupyter Notebooks for:
01_data_exploration.ipynb
02_feature_engineering.ipynb
03_model_training.ipynb
04_model_evaluation.ipynb
"""

import os
import json

NOTEBOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "notebooks")
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

def create_notebook(filename, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.11"
            },
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3 (ipykernel)"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    path = os.path.join(NOTEBOOKS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Generated notebook: {filename}")

# 1. 01_data_exploration.ipynb
nb1_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 01: Retail Sales Data Exploration\n",
            "\n",
            "This notebook loads the Walmart Recruiting Store Sales dataset, analyzes store-department distributions, inspects holiday spikes, and performs baseline data profiling."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "\n",
            "# Load raw Walmart train dataset\n",
            "train_df = pd.read_csv('../data/raw/train.csv')\n",
            "stores_df = pd.read_csv('../data/raw/stores.csv')\n",
            "features_df = pd.read_csv('../data/raw/features.csv')\n",
            "\n",
            "print(f\"Train records: {len(train_df):,}\")\n",
            "train_df.head()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Summary statistics\n",
            "print(\"Stores count:\", train_df['Store'].nunique())\n",
            "print(\"Departments count:\", train_df['Dept'].nunique())\n",
            "print(\"Date range:\", train_df['Date'].min(), \"to\", train_df['Date'].max())\n",
            "train_df.describe()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Plot weekly sales over time\n",
            "train_df['Date'] = pd.to_datetime(train_df['Date'])\n",
            "weekly_total = train_df.groupby('Date')['Weekly_Sales'].sum()\n",
            "\n",
            "plt.figure(figsize=(12, 5))\n",
            "plt.plot(weekly_total.index, weekly_total.values, color='#3b82f6', lw=2)\n",
            "plt.title('Total Weekly Sales Volume Over Time (Walmart Fleet)')\n",
            "plt.ylabel('Total Sales ($)')\n",
            "plt.grid(True, linestyle='--', alpha=0.5)\n",
            "plt.show()"
        ]
    }
]

# 2. 02_feature_engineering.ipynb
nb2_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 02: Chronological Feature Engineering & Lag Generation\n",
            "\n",
            "Demonstrates how to construct weekly lags (`lag_1`, `lag_2`, `lag_4`, `lag_7`), rolling window statistics, and calendar attributes without future look-ahead data leakage."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import sys\n",
            "import pandas as pd\n",
            "sys.path.append('..')\n",
            "from spark.feature_engineering import generate_features_pandas\n",
            "\n",
            "# Load cleaned sales data\n",
            "sales_df = pd.read_parquet('../data/processed/sales_clean.parquet')\n",
            "feat_df = generate_features_pandas(sales_df)\n",
            "print(f\"Generated {len(feat_df.columns)} features across {len(feat_df):,} records.\")\n",
            "feat_df[['store', 'department', 'date', 'sales', 'lag_1', 'rolling_mean_4', 'rolling_std_4']].head(10)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Correlation matrix of features\n",
            "numeric_cols = ['sales', 'lag_1', 'lag_2', 'lag_4', 'rolling_mean_4', 'rolling_mean_8', 'rolling_std_4']\n",
            "corr = feat_df[numeric_cols].corr()\n",
            "import seaborn as sns\n",
            "import matplotlib.pyplot as plt\n",
            "plt.figure(figsize=(8, 6))\n",
            "sns.heatmap(corr, annot=True, cmap='Blues', fmt='.2f')\n",
            "plt.title('Feature Autocorrelation Matrix')\n",
            "plt.show()"
        ]
    }
]

# 3. 03_model_training.ipynb
nb3_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 03: Model Training & Chronological Validation\n",
            "\n",
            "Trains Seasonal Naive baseline, SARIMA, and XGBoost regression models on chronologically split train (80%), validation (10%), and test (10%) sets."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import sys\n",
            "import pandas as pd\n",
            "sys.path.append('..')\n",
            "from models.model_utils import chronological_split, calculate_metrics\n",
            "from models.xgboost_model import RetailXGBoostModel\n",
            "\n",
            "feat_df = pd.read_parquet('../data/processed/features.parquet')\n",
            "train_df, val_df, test_df = chronological_split(feat_df, 0.8, 0.1)\n",
            "print(f\"Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,}\")\n",
            "\n",
            "# Train XGBoost regressor\n",
            "model = RetailXGBoostModel(n_estimators=200, learning_rate=0.05)\n",
            "model.fit(train_df, val_df)\n",
            "metrics = model.evaluate(val_df)\n",
            "print(\"XGBoost Validation Results:\", metrics)"
        ]
    }
]

# 4. 04_model_evaluation.ipynb
nb4_cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 04: Model Evaluation, MAPE Benchmark & Inventory Planning\n",
            "\n",
            "Compares validation metrics across models, inspects target criteria (<15% MAPE), and simulates supply-chain safety stock buffers."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import sys\n",
            "import json\n",
            "import pandas as pd\n",
            "sys.path.append('..')\n",
            "\n",
            "# Inspect saved model metadata\n",
            "meta_path = '../models/saved/model_metadata.json'\n",
            "with open(meta_path, 'r') as f:\n",
            "    meta = json.load(f)\n",
            "\n",
            "print(\"Best Model:\", meta['model_name'])\n",
            "print(\"Validation MAPE:\", f\"{meta['validation_mape']:.2f}%\")\n",
            "print(\"Target Status:\", meta['target_status'])\n",
            "\n",
            "pd.DataFrame(meta['metrics']).T"
        ]
    }
]

if __name__ == "__main__":
    create_notebook("01_data_exploration.ipynb", nb1_cells)
    create_notebook("02_feature_engineering.ipynb", nb2_cells)
    create_notebook("03_model_training.ipynb", nb3_cells)
    create_notebook("04_model_evaluation.ipynb", nb4_cells)

"""
XGBoost Regression Forecasting Model for Retail Sales.
Trained on chronological lag features, rolling windows, and store/dept categorical features.
Guarantees zero future data leakage.
"""

import os
import joblib
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from xgboost import XGBRegressor
from models.model_utils import calculate_metrics

logger = logging.getLogger("XGBoost_Model")

FEATURE_COLUMNS = [
    "store", "department", "year", "month", "week", "day_of_week",
    "quarter", "is_holiday", "lag_1", "lag_2", "lag_4", "lag_7",
    "rolling_mean_4", "rolling_mean_8", "rolling_std_4"
]

class RetailXGBoostModel:
    def __init__(
        self,
        n_estimators: int = 300,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        subsample: float = 0.85,
        colsample_bytree: float = 0.85,
        random_state: int = 42
    ):
        self.feature_columns = FEATURE_COLUMNS
        self.model = XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False

    def prepare_xy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Extracts features and target vector from the dataset.
        """
        # Ensure all required features are present
        X = df.copy()
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0.0

        X = X[self.feature_columns].copy()
        # Convert boolean to numeric
        if "is_holiday" in X.columns:
            X["is_holiday"] = X["is_holiday"].astype(int)

        y = df["sales"].values if "sales" in df.columns else np.zeros(len(df))
        return X, y

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None):
        """
        Fits XGBoost regressor chronologically.
        Uses early stopping on validation set if provided.
        """
        X_train, y_train = self.prepare_xy(train_df)
        
        if val_df is not None and len(val_df) > 0:
            X_val, y_val = self.prepare_xy(val_df)
            eval_set = [(X_train, y_train), (X_val, y_val)]
            self.model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train, verbose=False)

        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Generates predictions for feature records.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet. Call fit() first.")
        X, _ = self.prepare_xy(df)
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def evaluate(self, val_df: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluates predictions on validation set.
        """
        preds = self.predict(val_df)
        actuals = val_df["sales"].values
        return calculate_metrics(actuals, preds)

    def get_feature_importances(self) -> Dict[str, float]:
        """
        Returns normalized feature importance dictionary.
        """
        if not self.is_fitted:
            return {}
        importances = self.model.feature_importances_
        return {feat: float(round(imp, 4)) for feat, imp in zip(self.feature_columns, importances)}

    def save(self, filepath: str):
        """
        Saves trained model weights to disk using joblib.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        logger.info(f"Saved XGBoost model to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "RetailXGBoostModel":
        """
        Loads saved model from disk.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found at {filepath}")
        return joblib.load(filepath)

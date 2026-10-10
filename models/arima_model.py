"""
ARIMA / SARIMA & Seasonal Naive Forecasting Models.
Uses statsmodels for statistical time-series forecasting across Store & Department combinations.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from models.model_utils import calculate_metrics

logger = logging.getLogger("ARIMA_Model")

class SeasonalNaiveModel:
    """
    Seasonal Naive baseline forecasting model:
    Predicts sales at time t by taking the observation from the previous seasonal cycle (s periods ago).
    """
    def __init__(self, seasonality: int = 52):
        self.seasonality = seasonality
        self.history = None

    def fit(self, series: pd.Series):
        self.history = series.values
        return self

    def predict(self, steps: int) -> np.ndarray:
        if len(self.history) < self.seasonality:
            # Fallback to standard naive (last observed value) if history is shorter than seasonality
            last_val = self.history[-1] if len(self.history) > 0 else 0.0
            return np.full(steps, last_val)

        predictions = []
        for i in range(steps):
            idx = -(self.seasonality - (i % self.seasonality))
            if abs(idx) <= len(self.history):
                predictions.append(self.history[idx])
            else:
                predictions.append(self.history[-1])
        return np.array(predictions)

class RetailARIMAModel:
    """
    ARIMA / SARIMA Model for a specific store and department sales series.
    Supports configurable orders, seasonal patterns, and graceful convergence fallbacks.
    """
    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (1, 0, 0, 52),
        use_seasonal: bool = True
    ):
        self.order = order
        self.seasonal_order = seasonal_order
        self.use_seasonal = use_seasonal
        self.fitted_model = None
        self.last_date = None
        self.series = None

    def fit(self, series: pd.Series):
        """
        Fits the ARIMA or SARIMA model on the series.
        """
        self.series = series.copy()
        
        # Clean series: fill NAs with forward fill then 0
        cleaned = series.ffill().fillna(0.0)

        # Ensure we have enough data points for seasonal order
        s_period = self.seasonal_order[3] if self.seasonal_order else 1
        can_use_seasonal = self.use_seasonal and len(cleaned) >= (2 * s_period)

        try:
            if can_use_seasonal:
                model = SARIMAX(
                    cleaned.values,
                    order=self.order,
                    seasonal_order=self.seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                self.fitted_model = model.fit(disp=False)
            else:
                model = ARIMA(cleaned.values, order=self.order)
                self.fitted_model = model.fit()
        except Exception as exc:
            logger.warning(f"ARIMA fit failed with error: {exc}. Retrying with basic ARIMA(1, 1, 0)...")
            try:
                model = ARIMA(cleaned, order=(1, 1, 0))
                self.fitted_model = model.fit()
            except Exception as e:
                logger.error(f"Fallback ARIMA also failed: {e}. Model will use historical mean.")
                self.fitted_model = None

        return self

    def predict(self, steps: int = 7) -> np.ndarray:
        """
        Predicts future sales for the specified number of periods.
        """
        if self.fitted_model is not None:
            try:
                preds = self.fitted_model.forecast(steps=steps)
                # Ensure non-negative retail sales
                return np.maximum(0.0, np.asarray(preds))
            except Exception as e:
                logger.warning(f"Forecast generation failed: {e}. Falling back to historical mean.")

        # Fallback if fit failed
        if self.series is not None and len(self.series) > 0:
            mean_val = float(self.series.mean())
            return np.full(steps, max(0.0, mean_val))
        return np.zeros(steps)

    def evaluate(self, train_series: pd.Series, val_series: pd.Series) -> Dict[str, float]:
        """
        Fits on train_series and evaluates on val_series.
        Returns MAE, RMSE, safe MAPE.
        """
        self.fit(train_series)
        steps = len(val_series)
        preds = self.predict(steps=steps)
        metrics = calculate_metrics(val_series.values, preds)
        return metrics

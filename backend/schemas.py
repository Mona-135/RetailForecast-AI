"""
Pydantic schemas for request validation and response serialization.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# STORES
class StoreBase(BaseModel):
    store_id: int
    store_type: str = "A"
    size: int = 100000

class StoreOut(StoreBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# DEPARTMENTS
class DepartmentBase(BaseModel):
    department_id: int
    department_name: str

class DepartmentOut(DepartmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# SALES
class SaleBase(BaseModel):
    store_id: int
    department_id: int
    sales_date: date
    sales: float
    is_holiday: bool = False

class SaleOut(SaleBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# FORECASTS
class ForecastBase(BaseModel):
    store_id: int
    department_id: int
    forecast_date: date
    predicted_sales: float
    model_name: str = "XGBoost"

class ForecastOut(ForecastBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ForecastRunRequest(BaseModel):
    store_id: int = Field(default=1, ge=1)
    department_id: int = Field(default=1, ge=1)
    horizon: int = Field(default=7, ge=1, le=52)
    lead_time: int = Field(default=2, ge=1, le=12)
    service_level: float = Field(default=0.95, ge=0.80, le=0.999)

class ForecastRunResponse(BaseModel):
    status: str
    store_id: int
    department_id: int
    forecast_horizon: int
    mode: str
    forecasts: List[Dict[str, Any]]
    inventory_plan: Dict[str, Any]

# MODEL METRICS
class ModelMetricOut(BaseModel):
    id: int
    model_name: str
    store_id: int
    department_id: int
    mae: float
    rmse: float
    mape: float
    training_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# INVENTORY RECOMMENDATIONS
class InventoryRecommendationOut(BaseModel):
    id: int
    store_id: int
    department_id: int
    forecast_demand: float
    safety_stock: float
    reorder_point: float
    current_inventory: float
    status: str
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# DASHBOARD SUMMARY
class DashboardSummaryOut(BaseModel):
    total_stores: int
    total_departments: int
    total_sales: float
    average_sales: float
    best_model: str
    current_mape: float
    target_status: str
    target_achieved: bool
    number_of_low_stock_items: int
    number_of_overstock_items: int
    data_frequency: str = "weekly"
    last_updated: Optional[datetime] = None

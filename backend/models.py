"""
SQLAlchemy ORM models for PostgreSQL database.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, unique=True, nullable=False, index=True)
    store_type = Column(String(10), nullable=False, default="A")
    size = Column(Integer, nullable=False, default=100000)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="store", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="store", cascade="all, delete-orphan")
    inventory = relationship("InventoryRecommendation", back_populates="store", cascade="all, delete-orphan")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, unique=True, nullable=False, index=True)
    department_name = Column(String(100), nullable=False, default="Department")

    sales = relationship("Sale", back_populates="department", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="department", cascade="all, delete-orphan")
    inventory = relationship("InventoryRecommendation", back_populates="department", cascade="all, delete-orphan")

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False, index=True)
    sales_date = Column(Date, nullable=False, index=True)
    sales = Column(Float, nullable=False)
    is_holiday = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    store = relationship("Store", back_populates="sales")
    department = relationship("Department", back_populates="sales")

    __table_args__ = (
        UniqueConstraint("store_id", "department_id", "sales_date", name="uq_store_dept_date"),
        Index("idx_sales_store_dept_date", "store_id", "department_id", "sales_date"),
    )

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    predicted_sales = Column(Float, nullable=False)
    model_name = Column(String(50), nullable=False, default="XGBoost", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    store = relationship("Store", back_populates="forecasts")
    department = relationship("Department", back_populates="forecasts")

    __table_args__ = (
        UniqueConstraint("store_id", "department_id", "forecast_date", "model_name", name="uq_forecast_entry"),
        Index("idx_forecast_lookup", "store_id", "department_id", "forecast_date"),
    )

class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False, index=True)
    store_id = Column(Integer, nullable=False)
    department_id = Column(Integer, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_metrics_lookup", "model_name", "store_id", "department_id"),
    )

class InventoryRecommendation(Base):
    __tablename__ = "inventory_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_demand = Column(Float, nullable=False)
    safety_stock = Column(Float, nullable=False)
    reorder_point = Column(Float, nullable=False)
    current_inventory = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # LOW STOCK, NORMAL, OVERSTOCK
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    store = relationship("Store", back_populates="inventory")
    department = relationship("Department", back_populates="inventory")

    __table_args__ = (
        UniqueConstraint("store_id", "department_id", name="uq_inv_rec_store_dept"),
    )

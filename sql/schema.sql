-- Retail Sales Forecasting & Inventory Planning Database Schema
-- Compatible with PostgreSQL 13+ (and SQLite via SQLAlchemy)

-- 1. STORES TABLE
CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL UNIQUE,
    store_type VARCHAR(10) NOT NULL DEFAULT 'A',
    size INTEGER NOT NULL DEFAULT 100000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. DEPARTMENTS TABLE
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL UNIQUE,
    department_name VARCHAR(100) NOT NULL DEFAULT 'General Merchandise'
);

-- 3. HISTORICAL SALES TABLE
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    sales_date DATE NOT NULL,
    sales NUMERIC(14, 2) NOT NULL,
    is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_store_dept_date UNIQUE (store_id, department_id, sales_date)
);

-- 4. FORECASTS TABLE
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    predicted_sales NUMERIC(14, 2) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_forecast_store_dept_date_model UNIQUE (store_id, department_id, forecast_date, model_name)
);

-- 5. MODEL METRICS TABLE
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    store_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    mae NUMERIC(10, 4) NOT NULL,
    rmse NUMERIC(10, 4) NOT NULL,
    mape NUMERIC(8, 4) NOT NULL,
    training_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. INVENTORY RECOMMENDATIONS TABLE (Calculated inventory buffer and status)
CREATE TABLE IF NOT EXISTS inventory_recommendations (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    forecast_demand NUMERIC(14, 2) NOT NULL,
    safety_stock NUMERIC(14, 2) NOT NULL,
    reorder_point NUMERIC(14, 2) NOT NULL,
    current_inventory NUMERIC(14, 2) NOT NULL,
    status VARCHAR(20) NOT NULL, -- LOW STOCK, NORMAL, OVERSTOCK
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inv_store_dept UNIQUE (store_id, department_id)
);

-- INDEXES FOR FAST QUERYING AND FILTERING
CREATE INDEX IF NOT EXISTS idx_sales_store ON sales(store_id);
CREATE INDEX IF NOT EXISTS idx_sales_dept ON sales(department_id);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sales_date);
CREATE INDEX IF NOT EXISTS idx_sales_store_dept_date ON sales(store_id, department_id, sales_date);

CREATE INDEX IF NOT EXISTS idx_forecasts_store ON forecasts(store_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_dept ON forecasts(department_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_date ON forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_model ON forecasts(model_name);

CREATE INDEX IF NOT EXISTS idx_metrics_model ON model_metrics(model_name);
CREATE INDEX IF NOT EXISTS idx_metrics_store_dept ON model_metrics(store_id, department_id);

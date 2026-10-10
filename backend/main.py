"""
FastAPI Application Entry Point.
Provides RESTful APIs for Retail Sales Forecasting and Inventory Planning.
Includes Swagger UI documentation, CORS middleware, error handling, and health probes.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db
from backend.routers import stores, sales, forecasts, metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [FastAPI] %(message)s"
)
logger = logging.getLogger("FastAPI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database schema
    logger.info("Initializing database schema on startup...")
    try:
        init_db()
    except Exception as exc:
        logger.error(f"Error initializing DB schema: {exc}")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="Retail Sales Forecasting & Inventory Planning API",
    description="""
    End-to-End Big Data & Machine Learning System for Walmart Sales Forecasting.
    
    ### Key Features:
    - **Apache Kafka** streaming ingestion
    - **Hadoop HDFS** distributed storage
    - **Apache Spark** feature engineering and ETL
    - **XGBoost & SARIMA** demand forecasting
    - **Supply Chain Inventory Optimization** (Safety Stock & Reorder Points)
    - **Safe MAPE** evaluation
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(stores.router)
app.include_router(sales.router)
app.include_router(forecasts.router)
app.include_router(metrics.router)

# Base probe endpoints
@app.get("/", tags=["System Probes"])
def root():
    return {
        "system": "Retail Sales Forecasting and Inventory Planning",
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.get("/health", tags=["System Probes"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "kafka": "configured",
        "hdfs": "configured"
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

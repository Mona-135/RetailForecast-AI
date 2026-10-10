"""
Database engine and session management.
Connects to PostgreSQL as primary database, with automatic fallback
to local SQLite storage if PostgreSQL is offline during standalone development.
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
logger = logging.getLogger("Database")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/retail_forecasting")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
SQLITE_FALLBACK_URL = os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./data/retail_forecasting.db")

engine = None
SessionLocal = None
Base = declarative_base()

def get_engine():
    global engine, SessionLocal
    if engine is not None:
        return engine

    # Attempt PostgreSQL connection
    try:
        pg_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 3} if "postgresql" in DATABASE_URL else {}
        )
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to PostgreSQL database.")
        engine = pg_engine
    except Exception as exc:
        logger.warning(f"PostgreSQL connection failed ({exc}). Falling back to local SQLite database: {SQLITE_FALLBACK_URL}")
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"), exist_ok=True)
        sqlite_engine = create_engine(
            SQLITE_FALLBACK_URL,
            connect_args={"check_same_thread": False}
        )
        engine = sqlite_engine

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

# Initialize engine and SessionLocal on module load
get_engine()

def get_db():
    if SessionLocal is None:
        get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    eng = get_engine()
    from backend import models  # Ensure all SQLAlchemy models are registered
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables verified and initialized.")

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Get DATABASE_URL from environment, fallback to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Default to SQLite for development
    DATABASE_URL = "sqlite:///./trading.db"
    logger.warning("DATABASE_URL not set, using SQLite default: ./trading.db")
    logger.warning("For production, set DATABASE_URL environment variable")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

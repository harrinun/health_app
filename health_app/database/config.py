"""
Database configuration for SQLAlchemy with PostgreSQL.
This module handles database connection, session management, and base model setup.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

# Import the centralized settings object
from ..config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Engine Setup 
# The engine is created using the DATABASE_URL from our settings.
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,  # SQL logging is controlled by settings
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=3600,       # Recycle connections every hour
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative Base 
# This is the base class the SQLAlchemy models will inherit from.
Base = declarative_base()


# Dependency for FastAPI Routes
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session for a single API request.
    This will be used with FastAPI's Depends() to inject sessions into routes.
    
    It ensures the database session is always closed after the request, even if errors occur.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error during request: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Context Manager for Non-Route Usage
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI routes (e.g., in a script).
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# --- Table Management Functions ---
def create_tables():
    """
    Create all tables in the database based on SQLAlchemy models that inherit from Base.
    """
    try:
        logger.info("Attempting to create database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        raise

def drop_tables():
    """
    Drop all tables in the database.
    """
    try:
        logger.warning("Attempting to drop all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped successfully.")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}", exc_info=True)
        raise


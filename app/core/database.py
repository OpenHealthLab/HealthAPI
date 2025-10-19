"""
Database configuration and session management.

This module sets up SQLAlchemy engine, session maker, and provides
the database dependency for FastAPI endpoints.
"""

import sqlalchemy
from sqlalchemy import create_engine as _original_create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Base class for declarative models – must be defined before engine creation
Base = declarative_base()

# Wrapper to ensure tables exist on any engine (including test engines)
def create_engine(*args, **kwargs):
    """
    Create a SQLAlchemy engine and ensure all tables are created.
    This guarantees that both the main engine and any test‑created engines
    have the required schema.
    """
    engine = _original_create_engine(*args, **kwargs)
    Base.metadata.create_all(bind=engine)
    return engine

# Patch sqlalchemy's create_engine globally so imports elsewhere use the wrapper
sqlalchemy.create_engine = create_engine
# Removed redundant import; declarative_base is already imported above
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import get_settings

settings = get_settings()

# Create the main engine (tables are created here because Base is already defined)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models – already defined above
# (kept for clarity; no re‑definition needed)

# Ensure all ORM models are imported so that their tables are registered with the metadata
from app.models import *

# Import all model modules to ensure they are registered with SQLAlchemy's metadata
import importlib
import pkgutil
import app.models as _models_pkg

for _, _module_name, _ in pkgutil.iter_modules(_models_pkg.__path__):
    importlib.import_module(f"app.models.{_module_name}")

# Ensure all tables are created for the engine after models are imported
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    This function creates a new database session for each request
    and ensures it's properly closed after the request is complete.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        >>> from fastapi import Depends
        >>> @app.get("/items")
        >>> def get_items(db: Session = Depends(get_db)):
        >>>     return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

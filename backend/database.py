"""
Database connection and session management.

Supports SQLite (local dev) and PostgreSQL + pgvector (production).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    # SQLite needs check_same_thread=False for FastAPI
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined in models.py."""
    from backend.models import Resume, ResumeAnalysis  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("  Database tables created.")

"""
Database connection and session management.

Supports SQLite (local dev) and PostgreSQL + pgvector (production).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings

is_postgres = "postgresql" in settings.DATABASE_URL

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    # SQLite needs check_same_thread=False for FastAPI
    connect_args={"check_same_thread": False} if not is_postgres else {},
    pool_pre_ping=True if is_postgres else False,
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
    """Create all tables defined in models.py. Enable pgvector for PostgreSQL."""
    from backend.models import Resume, ResumeAnalysis  # noqa: F401

    # Enable pgvector extension on PostgreSQL
    if is_postgres:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("  pgvector extension enabled.")

    Base.metadata.create_all(bind=engine)
    db_type = "PostgreSQL" if is_postgres else "SQLite"
    print(f"  Database tables created ({db_type}).")

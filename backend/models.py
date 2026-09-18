"""
SQLAlchemy ORM models for the Resume Intelligence database.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from backend.database import Base, is_postgres

# Use pgvector's Vector type on PostgreSQL, JSON fallback on SQLite
if is_postgres:
    try:
        from pgvector.sqlalchemy import Vector
        VectorColumn = lambda dim: Column(Vector(dim))
    except ImportError:
        VectorColumn = lambda dim: Column(JSON)
else:
    VectorColumn = lambda dim: Column(JSON)


class Resume(Base):
    """A single resume or cover letter file."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(Text, nullable=False)
    folder = Column(Text)
    extension = Column(String(10))
    size_kb = Column(Float)
    modified_at = Column(String(50))
    doc_type = Column(String(20))       # 'Resume' or 'Cover Letter'
    content_text = Column(Text)
    word_count = Column(Integer)
    content_hash = Column(String(64), unique=True)  # SHA256 for dedup
    companies = Column(JSON, default=list)
    best_role = Column(String(100))
    best_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
    chunks = relationship("ResumeChunk", back_populates="resume", cascade="all, delete-orphan")


class ResumeAnalysis(Base):
    """Analysis of a resume against a specific role."""
    __tablename__ = "resume_analyses"
    __table_args__ = (
        UniqueConstraint("resume_id", "role_name", name="uq_resume_role"),
    )

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    role_name = Column(String(100), nullable=False)
    score = Column(Integer)
    label = Column(String(20))
    breakdown = Column(JSON)
    keywords_data = Column(JSON)    # Full keyword analysis
    coverage_pct = Column(Float)
    tips = Column(JSON)

    # Relationships
    resume = relationship("Resume", back_populates="analyses")


class ResumeChunk(Base):
    """A chunk of resume text with its vector embedding for RAG."""
    __tablename__ = "resume_chunks"
    __table_args__ = (
        UniqueConstraint("resume_id", "chunk_index", name="uq_resume_chunk"),
    )

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = VectorColumn(768)  # nomic-embed-text produces 768-dim

    # Relationships
    resume = relationship("Resume", back_populates="chunks")


class ChatMessage(Base):
    """Chat history for the resume Q&A feature."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)   # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    context_chunks = Column(JSON)               # which chunks were used as context
    created_at = Column(DateTime, default=datetime.utcnow)


"""
Application settings loaded from environment variables.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration — reads from .env file."""

    # Database
    DATABASE_URL: str = "sqlite:///./resume_intelligence.db"  # Default: local SQLite for dev

    # Ollama (local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # Resume scanning
    SCAN_ROOT: str = r"C:\Users\Rifat"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Paths
    PROJECT_ROOT: str = str(Path(__file__).parent.parent)
    LEGACY_CSV: str = str(Path(__file__).parent.parent / "resumes_found.csv")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

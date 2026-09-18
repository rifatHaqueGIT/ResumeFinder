"""
Jobs API — paste a job description and get AI-powered matching + gap analysis.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.rag import match_job
from backend.services.ollama import is_ollama_available

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobMatchRequest(BaseModel):
    title: str = ""
    company: str = ""
    description: str


class JobMatchResponse(BaseModel):
    analysis: str
    best_resumes: list[dict]
    sources: list[dict]


@router.post("/match", response_model=JobMatchResponse)
async def match_job_description(req: JobMatchRequest, db: Session = Depends(get_db)):
    """Paste a job description and get best resume match + gap analysis."""
    if not is_ollama_available():
        return JobMatchResponse(
            analysis="Ollama is not running. Please start it with 'ollama serve'.",
            best_resumes=[],
            sources=[],
        )

    # Build a richer query with title/company context
    query = req.description
    if req.title:
        query = f"Job Title: {req.title}\n{query}"
    if req.company:
        query = f"Company: {req.company}\n{query}"

    result = await match_job(query, db)
    return JobMatchResponse(**result)

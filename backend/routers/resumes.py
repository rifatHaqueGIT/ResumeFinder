"""
Resume API endpoints — CRUD + analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Resume, ResumeAnalysis
from backend.services.analyzer import ALL_ROLES

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.get("")
def list_resumes(db: Session = Depends(get_db)):
    """List all resumes with summary data and per-role scores."""
    resumes = db.query(Resume).order_by(Resume.best_score.desc().nullslast()).all()
    result = []

    for r in resumes:
        # Build role_scores dict from analyses
        role_scores = {}
        for analysis in r.analyses:
            role_scores[analysis.role_name] = analysis.score

        result.append({
            "id": r.id,
            "filename": r.filename,
            "extension": r.extension,
            "size_kb": r.size_kb,
            "modified_at": r.modified_at,
            "doc_type": r.doc_type,
            "companies": r.companies or [],
            "best_role": r.best_role,
            "best_score": r.best_score,
            "word_count": r.word_count,
            "role_scores": role_scores,
        })

    return result


@router.get("/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get full analysis for a specific resume across all roles."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Build role_analyses dict
    role_analyses = {}
    for analysis in resume.analyses:
        role_analyses[analysis.role_name] = {
            "score": analysis.score,
            "label": analysis.label,
            "breakdown": analysis.breakdown or {},
            "keywords": analysis.keywords_data or {},
            "coverage_pct": analysis.coverage_pct,
            "tips": analysis.tips or [],
        }

    return {
        "id": resume.id,
        "filename": resume.filename,
        "filepath": resume.filepath,
        "folder": resume.folder,
        "extension": resume.extension,
        "size_kb": resume.size_kb,
        "modified_at": resume.modified_at,
        "doc_type": resume.doc_type,
        "companies": resume.companies or [],
        "best_role": resume.best_role,
        "best_score": resume.best_score,
        "word_count": resume.word_count,
        "role_analyses": role_analyses,
    }

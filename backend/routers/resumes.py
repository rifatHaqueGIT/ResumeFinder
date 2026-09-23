"""
Resume API endpoints — CRUD + analysis + upload.
"""

from pathlib import Path
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Resume, ResumeAnalysis
from backend.services.analyzer import ALL_ROLES, analyze_resume_for_all_roles
from backend.services.scanner import extract_text, content_hash, detect_doc_type

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


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a new resume (PDF, DOCX, or TXT), parse, analyze, and save to DB."""
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: .pdf, .docx, .txt"
        )

    # Save to uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    save_path = uploads_dir / file.filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text(str(save_path.resolve()))
    if not text or len(text.strip()) < 30:
        raise HTTPException(
            status_code=400,
            detail="Could not extract readable text from the uploaded document."
        )

    c_hash = content_hash(text)
    existing = db.query(Resume).filter(
        (Resume.content_hash == c_hash) | (Resume.filename == file.filename)
    ).first()

    if existing:
        # Remove previous analysis to overwrite with updated upload
        db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == existing.id).delete()
        db.query(Resume).filter(Resume.id == existing.id).delete()
        db.commit()

    analysis = analyze_resume_for_all_roles(text, file.filename)
    file_size_kb = round(save_path.stat().st_size / 1024, 1)
    mod_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    resume = Resume(
        filename=file.filename,
        filepath=str(save_path.resolve()),
        folder=str(save_path.parent.resolve()),
        extension=ext,
        size_kb=file_size_kb,
        modified_at=mod_time,
        doc_type=detect_doc_type(file.filename),
        content_text=text,
        word_count=len(text.split()),
        content_hash=c_hash,
        companies=analysis["companies"],
        best_role=analysis["best_role"],
        best_score=analysis["best_score"],
    )
    db.add(resume)
    db.flush()

    for role in ALL_ROLES:
        role_data = analysis["role_analyses"][role]
        ra = ResumeAnalysis(
            resume_id=resume.id,
            role_name=role,
            score=role_data["score"],
            label=role_data["label"],
            breakdown=role_data["breakdown"],
            keywords_data=role_data["keywords"],
            coverage_pct=role_data["keywords"]["coverage_pct"],
            tips=role_data["tips"],
        )
        db.add(ra)

    db.commit()

    # Generate embeddings asynchronously if available
    try:
        from backend.services.embeddings import embed_resume
        await embed_resume(resume, db)
        db.commit()
    except Exception:
        pass

    return {
        "message": "Resume uploaded and analyzed successfully",
        "id": resume.id,
        "filename": resume.filename,
        "best_role": resume.best_role,
        "best_score": resume.best_score,
    }


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

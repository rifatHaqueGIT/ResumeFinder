"""
Role API endpoints — role definitions, rankings, keyword matrix.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Resume, ResumeAnalysis
from backend.services.analyzer import ALL_ROLES, ROLE_KEYWORDS

router = APIRouter(prefix="/api", tags=["roles"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """Return overview stats for the dashboard hero section."""
    all_resumes = db.query(Resume).all()
    resumes_only = [r for r in all_resumes if r.doc_type == "Resume"]
    covers_only = [r for r in all_resumes if r.doc_type == "Cover Letter"]

    # Best resume per role
    best_per_role = {}
    avg_scores = {}

    for role in ALL_ROLES:
        analyses = (
            db.query(ResumeAnalysis)
            .filter(ResumeAnalysis.role_name == role)
            .order_by(ResumeAnalysis.score.desc())
            .all()
        )

        if analyses:
            best = analyses[0]
            resume = db.query(Resume).filter(Resume.id == best.resume_id).first()
            if resume:
                best_per_role[role] = {
                    "filename": resume.filename,
                    "score": best.score,
                    "label": best.label,
                    "coverage": best.coverage_pct or 0,
                }

            # Avg score for resumes only (not cover letters)
            resume_ids = {r.id for r in resumes_only}
            role_scores = [a.score for a in analyses if a.resume_id in resume_ids]
            avg_scores[role] = round(sum(role_scores) / max(len(role_scores), 1), 1)
        else:
            avg_scores[role] = 0

    return {
        "total_resumes": len(resumes_only),
        "total_cover_letters": len(covers_only),
        "total_files": len(all_resumes),
        "roles": ALL_ROLES,
        "best_per_role": best_per_role,
        "avg_scores": avg_scores,
    }


@router.get("/roles")
def list_roles():
    """List all role definitions with their keyword categories."""
    return {role: keywords for role, keywords in ROLE_KEYWORDS.items()}


@router.get("/role/{role_name}")
def get_role_rankings(role_name: str, db: Session = Depends(get_db)):
    """Return all resumes ranked for a specific role."""
    if role_name not in ROLE_KEYWORDS:
        raise HTTPException(status_code=404, detail=f"Unknown role: {role_name}")

    analyses = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.role_name == role_name)
        .order_by(ResumeAnalysis.score.desc())
        .all()
    )

    ranked = []
    for a in analyses:
        resume = db.query(Resume).filter(Resume.id == a.resume_id).first()
        if not resume:
            continue

        kw_data = a.keywords_data or {}
        ranked.append({
            "id": resume.id,
            "filename": resume.filename,
            "doc_type": resume.doc_type,
            "score": a.score,
            "label": a.label,
            "coverage": a.coverage_pct or 0,
            "found": kw_data.get("total_found", 0),
            "total": kw_data.get("total_keywords", 0),
            "tips_count": len(a.tips or []),
        })

    return {
        "role": role_name,
        "keywords": ROLE_KEYWORDS[role_name],
        "resumes": ranked,
    }


@router.get("/keyword-matrix")
def get_keyword_matrix(db: Session = Depends(get_db)):
    """Return the keyword gap matrix for all roles and resumes."""
    resumes_only = db.query(Resume).filter(Resume.doc_type == "Resume").all()
    resume_names = [r.filename for r in resumes_only]

    # Preload ALL analyses in one query instead of N×M individual queries
    all_analyses = db.query(ResumeAnalysis).all()
    analysis_map = {}
    for a in all_analyses:
        analysis_map[(a.resume_id, a.role_name)] = a

    matrix = {}
    for role in ALL_ROLES:
        role_data = {}
        for category, keywords in ROLE_KEYWORDS[role].items():
            cat_data = []
            for kw in keywords:
                row = {"keyword": kw, "resumes": {}}
                for resume in resumes_only:
                    analysis = analysis_map.get((resume.id, role))
                    if analysis and analysis.keywords_data:
                        cats = analysis.keywords_data.get("categories", {})
                        cat_kws = cats.get(category, [])
                        kw_entry = next((k for k in cat_kws if k["keyword"] == kw), None)
                        row["resumes"][resume.filename] = kw_entry["found"] if kw_entry else False
                    else:
                        row["resumes"][resume.filename] = False
                cat_data.append(row)
            role_data[category] = cat_data
        matrix[role] = {"categories": role_data}

    return {"matrix": matrix, "resume_names": resume_names}


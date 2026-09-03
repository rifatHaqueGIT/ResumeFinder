"""
Seed the database with resume data from the legacy CSV.

Reads resumes_found.csv, extracts text, analyzes against all 4 roles,
and inserts into the SQLAlchemy database.

Usage:
    python -m scripts.seed_db
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from backend.config import settings
from backend.database import create_tables, SessionLocal
from backend.models import Resume, ResumeAnalysis
from backend.services.scanner import load_resumes_from_csv
from backend.services.analyzer import analyze_resume_for_all_roles, ALL_ROLES


def seed():
    print("\n  Resume Intelligence v2 — Database Seeder")
    print("  =========================================\n")

    # Create tables
    create_tables()

    # Load and extract resumes from CSV
    csv_path = settings.LEGACY_CSV
    print(f"\n  Loading from: {csv_path}\n")
    resume_data = load_resumes_from_csv(csv_path, max_workers=6)

    if not resume_data:
        print("  No resumes found. Make sure resumes_found.csv exists.")
        return

    db = SessionLocal()

    try:
        # Clear existing data
        db.query(ResumeAnalysis).delete()
        db.query(Resume).delete()
        db.commit()
        print(f"\n  Cleared existing data. Importing {len(resume_data)} resumes...\n")

        imported = 0
        for i, data in enumerate(resume_data):
            print(f"  [{i+1}/{len(resume_data)}] {data['filename']}")

            # Analyze against all 4 roles
            analysis = analyze_resume_for_all_roles(data["content_text"], data["filename"])

            # Create Resume record
            resume = Resume(
                filename=data["filename"],
                filepath=data["filepath"],
                folder=data["folder"],
                extension=data["extension"],
                size_kb=data["size_kb"],
                modified_at=data["modified"],
                doc_type=data["doc_type"],
                content_text=data["content_text"],
                word_count=data["word_count"],
                content_hash=data["content_hash"],
                companies=analysis["companies"],
                best_role=analysis["best_role"],
                best_score=analysis["best_score"],
            )
            db.add(resume)
            db.flush()  # Get the ID

            # Create ResumeAnalysis records for each role
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

            imported += 1

        db.commit()
        print(f"\n  Done! Imported {imported} resumes with {imported * len(ALL_ROLES)} role analyses.")

        # Summary stats
        for role in ALL_ROLES:
            top = (
                db.query(ResumeAnalysis)
                .filter(ResumeAnalysis.role_name == role)
                .order_by(ResumeAnalysis.score.desc())
                .first()
            )
            if top:
                resume = db.query(Resume).filter(Resume.id == top.resume_id).first()
                print(f"  {role}: top score = {top.score} ({resume.filename if resume else '?'})")

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR: {e}")
        raise
    finally:
        db.close()

    print("\n  Database seeded successfully!\n")


if __name__ == "__main__":
    seed()

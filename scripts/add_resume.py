"""
Add a single resume file to the database.

Usage:
    python -m scripts.add_resume "C:\\path\\to\\resume.pdf"
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from backend.database import SessionLocal, create_tables
from backend.models import Resume, ResumeAnalysis
from backend.services.scanner import process_single_file, detect_doc_type
from backend.services.analyzer import analyze_resume_for_all_roles, ALL_ROLES


def add_resume(filepath: str):
    p = Path(filepath)
    if not p.exists():
        print(f"Error: File not found: {filepath}")
        return None

    print(f"\nProcessing resume: {p.name}")
    data = process_single_file(str(p.resolve()))

    if not data:
        print(f"Error: Could not extract readable text from {filepath}. Ensure it is a valid PDF, DOCX, or TXT file.")
        return None

    data["doc_type"] = detect_doc_type(data["filename"])

    create_tables()
    db = SessionLocal()

    try:
        # Check if already exists by content_hash or filepath
        existing = db.query(Resume).filter(
            (Resume.content_hash == data["content_hash"]) | (Resume.filepath == data["filepath"])
        ).first()

        if existing:
            print(f"Warning: A resume matching this file/content already exists (ID: {existing.id}, {existing.filename}).")
            choice = input("Update existing record? (y/N): ").strip().lower()
            if choice == "y":
                db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == existing.id).delete()
                db.query(Resume).filter(Resume.id == existing.id).delete()
                db.commit()
                print("Removed previous record for update.")
            else:
                print("Aborting.")
                return existing.id

        # Analyze resume
        print("Analyzing resume against all target roles...")
        analysis = analyze_resume_for_all_roles(data["content_text"], data["filename"])

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
        print(f"Successfully added resume '{resume.filename}' (ID: {resume.id})!")
        print(f"  Best Role: {resume.best_role} ({resume.best_score}%)")

        # Try to generate embeddings if possible
        try:
            import asyncio
            from backend.services.embeddings import embed_resume
            print("Generating vector embeddings...")
            chunks_created = asyncio.run(embed_resume(resume, db))
            db.commit()
            print(f"  Created {chunks_created} embedding chunks.")
        except Exception as e:
            print(f"  Note: Embeddings skipped ({e}).")

        return resume.id

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a resume file to Resume Intelligence database.")
    parser.add_argument("filepath", help="Path to resume file (PDF, DOCX, TXT)")
    args = parser.parse_args()

    add_resume(args.filepath)

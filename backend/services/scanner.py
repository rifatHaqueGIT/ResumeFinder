"""
Resume file scanner — ported from legacy/resume_finder.py.

Extracts text from PDF, DOCX, TXT files and filters to Rifat's resumes.
Improved with parallel extraction and content deduplication.
"""

import hashlib
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_text_pdf(filepath: str) -> str:
    if not HAS_PYPDF2:
        return ""
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages[:10]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception:
        return ""


def extract_text_docx(filepath: str) -> str:
    if not HAS_DOCX:
        return ""
    try:
        doc = DocxDocument(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text_txt(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(100_000)
    except Exception:
        return ""


def extract_text(filepath: str) -> str:
    """Extract text content from a file based on its extension."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return extract_text_pdf(filepath)
    elif ext == ".docx":
        return extract_text_docx(filepath)
    elif ext in (".txt", ".rtf"):
        return extract_text_txt(filepath)
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# FILTERING
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns that indicate a file is NOT a resume
SKIP_PATTERNS = [
    "thirdpartylicense", "license", "log.txt", "build_log",
    "farming", "minecraft", "curseforge", "jre-legacy", "jre-x64",
    "case study", "essay", "module 3", "module 4",
    "power electronics", "converters",
    "change_of_enrolment", "medical_leave", "guarantor",
    "sublet", "volunteer agreement", "wochsublet",
    "abst participants", "study material",
    "individual licence", "visa statement", "employee contact",
    "1251_asg2", "asg3", "w25-657a",
    "ensf544 project", "predicting_price",
    "question_1_lean", "question_2_employee",
    "be 603", "be603", "a4.docx",
    "canadian canoe", "digital-transformation",
    "human resources policy", "student-programs-sde-transcript",
    "resume template", "resume toolkit",
]

OTHER_PEOPLE = ["nitish pradhan", "marco rossi", "volker wessels"]


def is_rifats_resume(filename: str, filepath: str, confidence: int = 0) -> bool:
    """Filter to only Rifat's own resumes and cover letters."""
    fname_lower = filename.lower()
    path_lower = filepath.lower()

    # Exclude known non-resumes
    for pattern in SKIP_PATTERNS:
        if pattern in fname_lower or pattern in path_lower:
            return False

    # Exclude other people's resumes
    for person in OTHER_PEOPLE:
        if person in fname_lower or person in path_lower:
            return False

    # Must have resume/cv signal
    resume_signals = ["resume", "cv", "cover letter", "cover_letter"]
    has_signal = any(s in fname_lower for s in resume_signals)

    # Must be in a Rifat-related path or have Rifat in filename
    rifat_signals = ["rifat", "haque", "\\resumes\\", "/resumes/", "\\res\\", "/res/"]
    is_rifats = any(s in path_lower for s in rifat_signals) or \
                any(s in fname_lower for s in ["rifat", "haque"])

    if has_signal and is_rifats:
        return True

    if confidence >= 60 and is_rifats:
        return True

    return False


def detect_doc_type(filename: str) -> str:
    """Determine if a file is a Resume or Cover Letter."""
    fname_lower = filename.lower()
    if "cover letter" in fname_lower or "cover_letter" in fname_lower:
        return "Cover Letter"
    return "Resume"


def content_hash(text: str) -> str:
    """SHA256 hash of text content for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# FILE METADATA
# ═══════════════════════════════════════════════════════════════════════════════

def get_file_metadata(filepath: str) -> dict:
    """Extract file metadata (size, modified date)."""
    try:
        stat = Path(filepath).stat()
        return {
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        }
    except OSError:
        return {"size_kb": 0, "modified": "Unknown"}


def process_single_file(filepath: str) -> dict | None:
    """Extract text and metadata from a single file. Returns None if extraction fails."""
    text = extract_text(filepath)
    if not text or len(text.strip()) < 30:
        return None

    p = Path(filepath)
    meta = get_file_metadata(filepath)

    return {
        "filepath": str(p),
        "filename": p.name,
        "folder": str(p.parent),
        "extension": p.suffix.lower(),
        "size_kb": meta["size_kb"],
        "modified": meta["modified"],
        "content_text": text,
        "word_count": len(text.split()),
        "content_hash": content_hash(text),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CSV LOADING (from legacy resumes_found.csv)
# ═══════════════════════════════════════════════════════════════════════════════

def load_resumes_from_csv(csv_path: str, max_workers: int = 4) -> list[dict]:
    """
    Load resumes from the legacy CSV, extract text with parallelism,
    filter to Rifat's files, and deduplicate by content hash.
    """
    import csv

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Loaded {len(rows)} entries from CSV")

    # Filter to files that exist and pass name-based filtering
    candidates = []
    for row in rows:
        filepath = row.get("path", "")
        filename = row.get("filename", "")
        confidence = int(row.get("confidence", 0))
        if os.path.exists(filepath) and is_rifats_resume(filename, filepath, confidence):
            candidates.append(row)

    print(f"  {len(candidates)} candidates after filtering")

    # Parallel text extraction
    results = []
    seen_hashes = set()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_row = {
            executor.submit(process_single_file, row["path"]): row
            for row in candidates
        }

        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                data = future.result()
                if data is None:
                    continue

                # Deduplicate by content hash
                if data["content_hash"] in seen_hashes:
                    continue
                seen_hashes.add(data["content_hash"])

                data["doc_type"] = detect_doc_type(data["filename"])
                results.append(data)
            except Exception as e:
                print(f"  Error processing {row.get('filename', '?')}: {e}")

    results.sort(key=lambda r: r["filename"])
    print(f"  {len(results)} unique resumes extracted")
    return results

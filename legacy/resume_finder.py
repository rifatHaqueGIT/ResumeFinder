r"""
Resume Finder — scans your computer for resume files, identifies them,
categorizes them, and outputs a clean summary.

Usage:
    python resume_finder.py                     # scan default path (C:\Users\Rifat)
    python resume_finder.py --path "D:\Docs"    # scan a custom path
    python resume_finder.py --deep              # also inspect file content (slower)
    python resume_finder.py --output results.csv  # save results to CSV
"""

import os
import sys
import argparse
import json
import csv
import re
import time
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows to avoid encoding errors
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from collections import defaultdict

# ─── Optional dependencies for content inspection ──────────────────────────────
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


# ─── Constants ──────────────────────────────────────────────────────────────────

RESUME_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt"}

# Filename patterns that strongly suggest a resume / CV
FILENAME_PATTERNS = [
    re.compile(r"\bresume\b", re.IGNORECASE),
    re.compile(r"\bcv\b", re.IGNORECASE),
    re.compile(r"\bcurriculum[\s_-]*vitae\b", re.IGNORECASE),
    re.compile(r"\bcover[\s_-]*letter\b", re.IGNORECASE),
]

# Keywords found *inside* resume content — grouped by category
CATEGORY_KEYWORDS = {
    "Software Engineering": [
        "software engineer", "developer", "full stack", "backend", "frontend",
        "python", "javascript", "java", "c++", "react", "node.js", "api",
        "git", "docker", "kubernetes", "ci/cd", "agile", "scrum",
    ],
    "Data Science / ML": [
        "data scientist", "machine learning", "deep learning", "tensorflow",
        "pytorch", "pandas", "numpy", "data analysis", "nlp", "computer vision",
        "statistical", "model training", "jupyter",
    ],
    "Product / Project Management": [
        "product manager", "project manager", "roadmap", "stakeholder",
        "sprint", "jira", "confluence", "kpi", "okr", "user stories",
    ],
    "Design / UX": [
        "ux designer", "ui designer", "figma", "sketch", "wireframe",
        "prototype", "user research", "usability", "design system",
    ],
    "Marketing": [
        "marketing", "seo", "content strategy", "social media", "brand",
        "google analytics", "campaign", "copywriting", "growth",
    ],
    "Finance / Accounting": [
        "financial analyst", "accounting", "cpa", "audit", "tax",
        "budgeting", "forecasting", "excel", "financial modeling",
    ],
    "General / Other": [
        "experience", "education", "skills", "references", "objective",
        "summary", "work history", "professional",
    ],
}

# Content keywords that confirm a file is likely a resume (not just named like one)
RESUME_CONTENT_SIGNALS = [
    "experience", "education", "skills", "objective", "summary",
    "work history", "professional", "references", "achievements",
    "certifications", "university", "bachelor", "master", "gpa",
    "linkedin", "phone", "email", "address",
]

# Directories to skip (performance + privacy)
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".idea", ".vscode", ".cache", "AppData", ".gradle", ".m2",
    "Library", ".Trash", "$Recycle.Bin", "Windows",
}


# ─── Styling helpers (ANSI colors) ─────────────────────────────────────────────

class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    MAGENTA = "\033[95m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    WHITE   = "\033[97m"
    BG_DARK = "\033[48;5;235m"

C = Colors


def banner():
    print(f"""
{C.CYAN}{C.BOLD}+{'=' * 58}+
|                   RESUME FINDER                          |
|          Scan - Identify - Categorize - Organize         |
+{'=' * 58}+{C.RESET}
""")


def section(title):
    print(f"\n{C.BOLD}{C.MAGENTA}{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}{C.RESET}")


# ─── File scanning ──────────────────────────────────────────────────────────────

def should_skip_dir(dirname):
    """Return True if this directory should be skipped."""
    return dirname in SKIP_DIRS or dirname.startswith(".")


def find_candidate_files(root_path):
    """Walk the filesystem and yield paths with resume-friendly extensions."""
    root = Path(root_path)
    if not root.exists():
        print(f"{C.RED}✗ Path does not exist: {root}{C.RESET}")
        sys.exit(1)

    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune skipped dirs in-place for performance
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext in RESUME_EXTENSIONS:
                full_path = Path(dirpath) / fname
                yield full_path
                scanned += 1

        # Progress indicator every 500 files
        if scanned > 0 and scanned % 500 == 0:
            print(f"  {C.DIM}...scanned {scanned} candidate files so far{C.RESET}", end="\r")


def score_filename(filepath):
    """Score how likely the filename indicates a resume (0-100)."""
    name = filepath.stem  # filename without extension
    score = 0
    for pattern in FILENAME_PATTERNS:
        if pattern.search(name):
            score += 60
            break

    # Bonus: short filenames with "resume" are very likely resumes
    if len(name) < 40:
        score += 5
    # Penalty: very long filenames are less likely
    if len(name) > 80:
        score -= 10

    return min(score, 100)


# ─── Content extraction ────────────────────────────────────────────────────────

def extract_text_pdf(filepath):
    """Extract text from a PDF file."""
    if not HAS_PYPDF2:
        return ""
    try:
        reader = PdfReader(str(filepath))
        text = ""
        for page in reader.pages[:5]:  # First 5 pages max
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception:
        return ""


def extract_text_docx(filepath):
    """Extract text from a DOCX file."""
    if not HAS_DOCX:
        return ""
    try:
        doc = DocxDocument(str(filepath))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text_txt(filepath):
    """Extract text from a plain text file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(50_000)  # First 50KB
    except Exception:
        return ""


def extract_text(filepath):
    """Extract text from a file based on its extension."""
    ext = filepath.suffix.lower()
    if ext == ".pdf":
        return extract_text_pdf(filepath)
    elif ext == ".docx":
        return extract_text_docx(filepath)
    elif ext in (".txt", ".rtf"):
        return extract_text_txt(filepath)
    return ""


def score_content(text):
    """Score how likely the content is a resume (0-100)."""
    if not text or len(text.strip()) < 50:
        return 0

    text_lower = text.lower()
    hits = sum(1 for kw in RESUME_CONTENT_SIGNALS if kw in text_lower)

    # Normalize: 6+ hits = very likely a resume
    score = min(int((hits / 6) * 80), 100)
    return score


def categorize(text):
    """Return the best-matching category for this resume based on content."""
    if not text:
        return "Uncategorized"

    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "General / Other":
            continue
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            scores[category] = hits

    if not scores:
        return "General / Other"

    return max(scores, key=scores.get)


# ─── Main logic ─────────────────────────────────────────────────────────────────

def analyze_files(root_path, deep=False):
    """Scan, score, and categorize resume candidates."""
    results = []
    start = time.time()

    print(f"  {C.CYAN}Scanning:{C.RESET} {root_path}")
    print(f"  {C.CYAN}Deep inspection:{C.RESET} {'Yes (reading file contents)' if deep else 'No (filename only — use --deep for content)'}")
    print()

    candidates = list(find_candidate_files(root_path))
    print(f"  {C.GREEN}Found {len(candidates)} files with resume-friendly extensions{C.RESET}")

    for filepath in candidates:
        fname_score = score_filename(filepath)
        content_score = 0
        category = "Uncategorized"
        text = ""

        if deep and fname_score >= 20:
            # Only inspect content for files with promising filenames
            text = extract_text(filepath)
            content_score = score_content(text)
            category = categorize(text)
        elif deep:
            # For non-promising filenames, still do a quick check
            text = extract_text(filepath)
            content_score = score_content(text)
            if content_score >= 40:
                category = categorize(text)

        # Combined confidence score
        if deep:
            total_score = int(fname_score * 0.4 + content_score * 0.6)
        else:
            total_score = fname_score
            if fname_score >= 40:
                category = "Uncategorized (run with --deep to categorize)"

        # Only include files with a meaningful score
        if total_score >= 20 or fname_score >= 40:
            try:
                stat = filepath.stat()
                size_kb = stat.st_size / 1024
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                size_kb = 0
                modified = "Unknown"

            results.append({
                "path": str(filepath),
                "filename": filepath.name,
                "extension": filepath.suffix.lower(),
                "size_kb": round(size_kb, 1),
                "modified": modified,
                "confidence": total_score,
                "category": category,
                "folder": str(filepath.parent),
            })

    elapsed = time.time() - start
    print(f"  {C.DIM}Scan completed in {elapsed:.1f}s{C.RESET}")
    return sorted(results, key=lambda r: r["confidence"], reverse=True)


def display_results(results):
    """Print a formatted summary of found resumes."""
    if not results:
        print(f"\n  {C.YELLOW}No resumes found. Try running with --deep or checking the scan path.{C.RESET}")
        return

    section(f"Found {len(results)} Resume(s)")

    # Group by category
    by_category = defaultdict(list)
    for r in results:
        by_category[r["category"]].append(r)

    for category, items in sorted(by_category.items()):
        print(f"\n  {C.BOLD}{C.BLUE}📁 {category}{C.RESET}  ({len(items)} file{'s' if len(items) != 1 else ''})")
        print(f"  {C.DIM}{'-' * 55}{C.RESET}")

        for item in items:
            conf = item["confidence"]
            if conf >= 60:
                conf_color = C.GREEN
                conf_icon = "🟢"
            elif conf >= 40:
                conf_color = C.YELLOW
                conf_icon = "🟡"
            else:
                conf_color = C.RED
                conf_icon = "🔴"

            print(f"    {conf_icon} {C.WHITE}{item['filename']}{C.RESET}")
            print(f"       {C.DIM}Path:       {item['path']}{C.RESET}")
            print(f"       {C.DIM}Size:       {item['size_kb']} KB  |  Modified: {item['modified']}{C.RESET}")
            print(f"       {conf_color}Confidence: {conf}%{C.RESET}")
            print()

    # Summary stats
    section("Summary")
    print(f"  {C.CYAN}Total resumes found:{C.RESET}  {len(results)}")
    print(f"  {C.CYAN}High confidence (≥60%):{C.RESET} {sum(1 for r in results if r['confidence'] >= 60)}")
    print(f"  {C.CYAN}Medium (40-59%):{C.RESET}        {sum(1 for r in results if 40 <= r['confidence'] < 60)}")
    print(f"  {C.CYAN}Low (<40%):{C.RESET}             {sum(1 for r in results if r['confidence'] < 40)}")

    ext_counts = defaultdict(int)
    for r in results:
        ext_counts[r["extension"]] += 1
    print(f"  {C.CYAN}By file type:{C.RESET}          ", end="")
    print("  ".join(f"{ext}: {count}" for ext, count in sorted(ext_counts.items())))
    print()


def save_results(results, output_path):
    """Save results to CSV or JSON based on file extension."""
    output = Path(output_path)

    if output.suffix.lower() == ".json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    else:
        # Default to CSV
        if not results:
            print(f"  {C.YELLOW}No results to save.{C.RESET}")
            return
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    print(f"  {C.GREEN}✓ Results saved to: {output}{C.RESET}")


# ─── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📄 Resume Finder — scan your computer for resume files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python resume_finder.py                          # Quick scan (filename only)
  python resume_finder.py --deep                   # Deep scan (reads file content)
  python resume_finder.py --path "D:\\Documents"    # Scan a custom folder
  python resume_finder.py --deep --output resumes.csv   # Save results to CSV
  python resume_finder.py --deep --output resumes.json  # Save results to JSON
        """,
    )
    parser.add_argument(
        "--path", "-p",
        default=r"C:\Users\Rifat",
        help="Root directory to scan (default: C:\\Users\\Rifat)",
    )
    parser.add_argument(
        "--deep", "-d",
        action="store_true",
        help="Inspect file content for smarter detection and categorization (slower)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Save results to a file (.csv or .json)",
    )
    parser.add_argument(
        "--min-confidence", "-c",
        type=int,
        default=20,
        help="Minimum confidence score to include (default: 20)",
    )

    args = parser.parse_args()

    banner()

    results = analyze_files(args.path, deep=args.deep)

    # Filter by minimum confidence
    results = [r for r in results if r["confidence"] >= args.min_confidence]

    display_results(results)

    if args.output:
        save_results(results, args.output)


if __name__ == "__main__":
    main()

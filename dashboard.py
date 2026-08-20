"""
Resume Intelligence Dashboard — Flask backend.

Serves a premium web dashboard that acts as an Expert Hiring Manager,
analyzing all of Rifat's resumes against 4 target roles.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

from flask import Flask, render_template, jsonify

# ── Reuse extraction functions from resume_analyzer ──────────────────────────
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
# ROLE DEFINITIONS — Expert HM keyword sets for the 4 target roles
# ═══════════════════════════════════════════════════════════════════════════════

ROLE_KEYWORDS = {
    "Software Engineer": {
        "Technical Skills": [
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "sql", "html", "css", "react", "angular", "vue", "node.js", "spring",
            "django", "flask", "fastapi", ".net", "rest api", "graphql",
        ],
        "DevOps & Tools": [
            "git", "docker", "kubernetes", "ci/cd", "jenkins", "github actions",
            "aws", "azure", "gcp", "terraform", "linux", "bash",
        ],
        "Core Competencies": [
            "data structures", "algorithms", "system design", "microservices",
            "object-oriented", "design patterns", "testing", "unit test",
            "agile", "scrum", "code review", "debugging",
        ],
        "Soft Skills & Impact": [
            "leadership", "teamwork", "collaboration", "communication",
            "problem solving", "mentoring", "cross-functional",
        ],
        "Experience Signals": [
            "internship", "co-op", "full-time", "contract",
            "project", "developed", "implemented", "built", "designed",
            "optimized", "reduced", "increased", "improved", "deployed",
        ],
    },
    "Full Stack Developer": {
        "Frontend": [
            "html", "css", "javascript", "typescript", "react", "angular", "vue",
            "next.js", "sass", "tailwind", "bootstrap", "responsive design",
            "webpack", "vite",
        ],
        "Backend": [
            "node.js", "express", "django", "flask", "spring", "fastapi",
            "rest api", "graphql", "authentication", "authorization",
            "microservices", "serverless",
        ],
        "Databases": [
            "sql", "postgresql", "mysql", "mongodb", "redis", "dynamodb",
            "orm", "database design", "migrations",
        ],
        "DevOps & Cloud": [
            "git", "docker", "kubernetes", "ci/cd", "aws", "azure", "gcp",
            "s3", "lambda", "ec2", "vercel", "netlify", "linux",
        ],
        "Testing & Quality": [
            "testing", "unit test", "jest", "cypress", "selenium",
            "tdd", "code review", "debugging", "agile", "scrum",
        ],
        "Impact & Experience": [
            "project", "developed", "implemented", "built", "designed",
            "deployed", "optimized", "reduced", "increased", "improved",
            "collaboration", "communication", "leadership",
        ],
    },
    "Data Scientist / ML Engineer": {
        "Core ML/AI": [
            "machine learning", "deep learning", "neural network", "nlp",
            "computer vision", "reinforcement learning", "generative ai",
            "tensorflow", "pytorch", "keras", "scikit-learn", "xgboost",
            "random forest", "gradient boosting", "transformer",
        ],
        "Data & Analytics": [
            "python", "r", "sql", "pandas", "numpy", "matplotlib", "seaborn",
            "jupyter", "tableau", "power bi", "spark", "hadoop", "etl",
            "data pipeline", "feature engineering", "a/b testing",
            "pyspark", "databricks",
        ],
        "Statistics & Math": [
            "statistics", "probability", "regression", "classification",
            "clustering", "dimensionality reduction", "hypothesis testing",
            "bayesian", "optimization", "cross-validation", "pca",
            "t-sne", "k-means",
        ],
        "MLOps & Tools": [
            "git", "docker", "aws", "mlflow", "airflow", "ci/cd",
            "model deployment", "api", "flask", "fastapi",
        ],
        "Soft Skills & Impact": [
            "communication", "presentation", "stakeholder",
            "research", "published", "accuracy", "improved", "reduced",
            "collaboration", "problem solving",
        ],
    },
    "Data Analyst": {
        "Technical Skills": [
            "sql", "python", "r", "excel", "vba", "power bi", "tableau",
            "looker", "google analytics", "pandas", "numpy",
        ],
        "Data Processing": [
            "etl", "data pipeline", "data cleaning", "data wrangling",
            "data modeling", "database", "postgresql", "mysql", "mongodb",
            "spark", "hadoop", "big data",
        ],
        "Analysis & Visualization": [
            "data analysis", "data visualization", "dashboard", "reporting",
            "matplotlib", "seaborn", "plotly", "charts", "kpi",
            "a/b testing", "hypothesis testing",
        ],
        "Statistics": [
            "statistics", "regression", "correlation", "probability",
            "forecasting", "trend analysis", "descriptive statistics",
            "inferential statistics",
        ],
        "Business & Communication": [
            "stakeholder", "presentation", "communication", "business intelligence",
            "requirements", "documentation", "insights", "recommendations",
            "decision making", "problem solving", "collaboration",
        ],
        "Impact & Experience": [
            "project", "developed", "implemented", "built", "analyzed",
            "improved", "reduced", "increased", "optimized", "automated",
        ],
    },
}

ALL_ROLES = list(ROLE_KEYWORDS.keys())

# Known companies to detect
KNOWN_COMPANIES = [
    "Google", "Amazon", "Meta", "Facebook", "Apple", "Microsoft", "Netflix",
    "TikTok", "ByteDance", "Stripe", "Shopify", "Uber", "Airbnb",
    "LinkedIn", "Salesforce", "Adobe", "Oracle", "IBM", "Intel", "Nvidia",
    "Tesla", "SpaceX", "DoorDash", "Lyft", "Coinbase", "Reddit", "Discord",
    "Atlassian", "GitHub", "GitLab", "MongoDB", "Snowflake",
    "Databricks", "Figma", "Notion", "Vercel",
    "Ubisoft", "UbiLab", "VistaVu", "YMCA", "Shaw", "Telus", "Rogers",
    "TD Bank", "RBC", "BMO", "Scotiabank", "CIBC", "Deloitte", "KPMG",
    "Accenture", "CGI", "SAP", "BlackBerry",
    "University of Calgary", "University of Waterloo",
    "Stripe", "DoorDash", "BWC",
]


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION (reused from resume_analyzer.py)
# ═══════════════════════════════════════════════════════════════════════════════

def extract_text_pdf(filepath):
    if not HAS_PYPDF2:
        return ""
    try:
        reader = PdfReader(str(filepath))
        text = ""
        for page in reader.pages[:10]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception:
        return ""


def extract_text_docx(filepath):
    if not HAS_DOCX:
        return ""
    try:
        doc = DocxDocument(str(filepath))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text_txt(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(100_000)
    except Exception:
        return ""


def extract_text(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return extract_text_pdf(filepath)
    elif ext == ".docx":
        return extract_text_docx(filepath)
    elif ext in (".txt", ".rtf"):
        return extract_text_txt(filepath)
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def detect_companies(text, filename):
    combined = text + " " + filename
    found = set()
    for company in KNOWN_COMPANIES:
        pattern = re.compile(r'\b' + re.escape(company) + r'\b', re.IGNORECASE)
        if pattern.search(combined):
            found.add(company)
    return sorted(found) if found else []


def analyze_keywords_for_role(text, role):
    """Return keyword analysis for a specific role."""
    role_kws = ROLE_KEYWORDS.get(role, {})
    text_lower = text.lower() if text else ""

    categories = {}
    total_found = 0
    total_keywords = 0

    for category, keywords in role_kws.items():
        results = []
        for kw in keywords:
            found = kw in text_lower
            results.append({"keyword": kw, "found": found})
            total_keywords += 1
            if found:
                total_found += 1
        categories[category] = results

    coverage = round((total_found / max(total_keywords, 1)) * 100, 1)

    return {
        "categories": categories,
        "total_found": total_found,
        "total_keywords": total_keywords,
        "coverage_pct": coverage,
    }


def score_resume_for_role(text, role):
    """
    Score a resume 0-100 for a specific role as an expert HM.

    Rubric:
      - Keyword coverage for role (0-30 pts)
      - Quantified achievements (0-20 pts)
      - Structure & sections (0-15 pts)
      - Education & credentials (0-15 pts)
      - Experience depth (0-10 pts)
      - Professional presentation (0-10 pts)
    """
    if not text or len(text.strip()) < 50:
        return 10, "Unable to extract content", {}

    text_lower = text.lower()
    score = 0
    breakdown = {}

    # 1. Keyword coverage (0-30)
    role_kws = ROLE_KEYWORDS.get(role, {})
    all_kws = []
    for cat_keywords in role_kws.values():
        all_kws.extend(cat_keywords)
    hits = sum(1 for kw in all_kws if kw in text_lower)
    kw_ratio = hits / max(len(all_kws), 1)
    kw_score = min(int(kw_ratio * 60), 30)
    score += kw_score
    breakdown["Keyword Coverage"] = {"score": kw_score, "max": 30,
                                      "detail": f"{hits}/{len(all_kws)} keywords found"}

    # 2. Quantified achievements (0-20)
    metrics_patterns = [
        r'\d+%', r'\$[\d,]+', r'\d+x\b', r'\d+\+?\s*(users|customers|clients)',
        r'reduced\s+\w+\s+by', r'increased\s+\w+\s+by', r'improved\s+\w+\s+by',
        r'saved\s+\w+', r'generated\s+\w+', r'managed\s+\w+\s+team',
        r'\d+\s*projects?', r'led\s+\w+\s+of\s+\d+',
    ]
    metric_hits = sum(1 for p in metrics_patterns if re.search(p, text_lower))
    metrics_score = min(metric_hits * 4, 20)
    score += metrics_score
    breakdown["Quantified Impact"] = {"score": metrics_score, "max": 20,
                                       "detail": f"{metric_hits} metric patterns found"}

    # 3. Structure (0-15)
    structure_signals = [
        "experience", "education", "skills", "projects", "summary",
        "objective", "work history", "technical skills", "achievements",
        "certifications", "awards", "publications", "volunteer",
    ]
    struct_hits = sum(1 for s in structure_signals if s in text_lower)
    struct_score = min(struct_hits * 3, 15)
    score += struct_score
    breakdown["Resume Structure"] = {"score": struct_score, "max": 15,
                                      "detail": f"{struct_hits} sections detected"}

    # 4. Education (0-15)
    edu_signals = [
        "bachelor", "master", "mba", "phd", "b.sc", "m.sc", "b.eng", "m.eng",
        "university", "college", "degree", "gpa", "dean's list", "honors",
        "certification", "certified", "aws certified", "pmp",
    ]
    edu_hits = sum(1 for e in edu_signals if e in text_lower)
    edu_score = min(edu_hits * 3, 15)
    score += edu_score
    breakdown["Education & Credentials"] = {"score": edu_score, "max": 15,
                                              "detail": f"{edu_hits} education signals"}

    # 5. Experience depth (0-10)
    date_ranges = len(re.findall(r'20\d{2}\s*[-\u2013]\s*(20\d{2}|present|current)', text_lower))
    exp_score = min(date_ranges * 3, 10)
    score += exp_score
    breakdown["Experience Depth"] = {"score": exp_score, "max": 10,
                                      "detail": f"{date_ranges} role date ranges"}

    # 6. Professional presentation (0-10)
    pro_signals = ["linkedin", "github", "portfolio", "email", "phone"]
    pro_hits = sum(1 for p in pro_signals if p in text_lower)
    pro_score = min(pro_hits * 2, 10)
    score += pro_score
    breakdown["Professional Presentation"] = {"score": pro_score, "max": 10,
                                                "detail": f"{pro_hits}/5 contact elements"}

    score = min(score, 100)

    # Penalize short resumes
    word_count = len(text.split())
    if word_count < 100:
        score = min(score, 35)
    elif word_count < 200:
        score = max(score - 10, 0)

    return score, _get_score_label(score), breakdown


def _get_score_label(score):
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Strong"
    elif score >= 50:
        return "Good"
    elif score >= 35:
        return "Needs Work"
    else:
        return "Weak"


def generate_tips(text, role, keyword_analysis):
    """Generate actionable resume improvement tips for a specific role."""
    tips = []
    text_lower = text.lower() if text else ""

    # Missing keywords by category
    for category, keywords in keyword_analysis["categories"].items():
        missing = [kw["keyword"] for kw in keywords if not kw["found"]]
        found = [kw["keyword"] for kw in keywords if kw["found"]]
        if missing and len(missing) > len(found):
            top_missing = missing[:5]
            tips.append({
                "type": "keyword_gap",
                "severity": "high" if len(missing) > len(found) * 2 else "medium",
                "category": category,
                "title": f"Add more {category} keywords",
                "description": f"Your resume is missing key {category.lower()} terms that hiring managers for {role} look for.",
                "keywords": top_missing,
            })
        elif missing:
            top_missing = missing[:3]
            tips.append({
                "type": "keyword_gap",
                "severity": "low",
                "category": category,
                "title": f"Consider adding {category} keywords",
                "description": f"A few {category.lower()} terms could strengthen your {role} application.",
                "keywords": top_missing,
            })

    # Quantified metrics check
    metrics_patterns = [r'\d+%', r'\$[\d,]+', r'\d+x\b']
    metric_hits = sum(1 for p in metrics_patterns if re.search(p, text_lower))
    if metric_hits < 3:
        tips.append({
            "type": "metrics",
            "severity": "high",
            "category": "Impact",
            "title": "Add more quantified achievements",
            "description": "Hiring managers love numbers. Quantify your impact: 'Reduced build time by 40%', 'Served 10K+ users', 'Managed team of 5'.",
            "keywords": [],
        })

    # Action verbs check
    strong_verbs = ["architected", "spearheaded", "engineered", "orchestrated", "streamlined"]
    used_strong = [v for v in strong_verbs if v in text_lower]
    if len(used_strong) < 2:
        tips.append({
            "type": "language",
            "severity": "medium",
            "category": "Language",
            "title": "Use stronger action verbs",
            "description": "Replace generic verbs like 'worked on' or 'responsible for' with power verbs.",
            "keywords": ["Architected", "Spearheaded", "Engineered", "Orchestrated", "Streamlined"],
        })

    # Professional presence
    if "linkedin" not in text_lower:
        tips.append({
            "type": "presentation",
            "severity": "medium",
            "category": "Presentation",
            "title": "Add your LinkedIn URL",
            "description": "Most hiring managers check LinkedIn. Include your profile URL in the header.",
            "keywords": [],
        })
    if "github" not in text_lower and role in ("Software Engineer", "Full Stack Developer"):
        tips.append({
            "type": "presentation",
            "severity": "medium",
            "category": "Presentation",
            "title": "Add your GitHub profile",
            "description": f"For {role} roles, a GitHub link with active projects significantly boosts credibility.",
            "keywords": [],
        })

    return tips


def is_rifats_resume(row, text):
    """Filter to only Rifat's own resumes and cover letters."""
    filename = row["filename"].lower()
    path = row["path"].lower()

    # Exclude obvious non-resumes
    skip_patterns = [
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
    for pattern in skip_patterns:
        if pattern in filename or pattern in path:
            return False

    # Exclude other people's resumes
    other_people = ["nitish pradhan", "marco rossi", "volker wessels"]
    for person in other_people:
        if person in filename.lower() or person in path.lower():
            return False

    # Must have resume/cv signal in filename
    resume_signals = ["resume", "cv", "cover letter", "cover_letter"]
    has_signal = any(s in filename for s in resume_signals)

    # Must be in a Rifat-related path or have Rifat in filename
    rifat_signals = ["rifat", "haque", "\\resumes\\", "/resumes/", "\\res\\", "/res/"]
    is_rifats = any(s in path for s in rifat_signals) or any(s in filename for s in ["rifat", "haque"])

    if has_signal and is_rifats:
        return True

    # High confidence + Rifat-related
    try:
        if int(row.get("confidence", 0)) >= 60 and is_rifats:
            return True
    except (ValueError, TypeError):
        pass

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING & PRECOMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

def load_and_analyze():
    """Load resumes from CSV and pre-compute all analysis."""
    csv_path = Path(__file__).parent / "resumes_found.csv"
    if not csv_path.exists():
        print("ERROR: resumes_found.csv not found. Run resume_finder.py --deep first.")
        return []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    print(f"  Loaded {len(all_rows)} entries from CSV")
    resumes = []

    for i, row in enumerate(all_rows):
        filepath = row["path"]
        if not os.path.exists(filepath):
            continue

        text = extract_text(filepath)
        if not is_rifats_resume(row, text):
            continue

        print(f"  Analyzing [{i+1}]: {row['filename']}")

        companies = detect_companies(text, row["filename"])

        # Determine document type
        fname_lower = row["filename"].lower()
        if "cover letter" in fname_lower or "cover_letter" in fname_lower:
            doc_type = "Cover Letter"
        else:
            doc_type = "Resume"

        # Analyze against ALL 4 roles
        role_analyses = {}
        for role in ALL_ROLES:
            kw_analysis = analyze_keywords_for_role(text, role)
            score, label, breakdown = score_resume_for_role(text, role)
            tips = generate_tips(text, role, kw_analysis)

            role_analyses[role] = {
                "score": score,
                "label": label,
                "breakdown": breakdown,
                "keywords": kw_analysis,
                "tips": tips,
            }

        # Find best-fit role
        best_role = max(ALL_ROLES, key=lambda r: role_analyses[r]["score"])

        resume_data = {
            "id": len(resumes),
            "filename": row["filename"],
            "path": row["path"],
            "folder": row["folder"],
            "extension": row["extension"],
            "size_kb": float(row["size_kb"]),
            "modified": row["modified"],
            "doc_type": doc_type,
            "companies": companies,
            "best_role": best_role,
            "best_score": role_analyses[best_role]["score"],
            "role_analyses": role_analyses,
            "word_count": len(text.split()) if text else 0,
        }
        resumes.append(resume_data)

    resumes.sort(key=lambda r: r["best_score"], reverse=True)
    # Re-index after sort
    for i, r in enumerate(resumes):
        r["id"] = i

    print(f"\n  {len(resumes)} of Rifat's resumes analyzed against {len(ALL_ROLES)} roles.")
    return resumes


# ═══════════════════════════════════════════════════════════════════════════════
# FLASK APP
# ═══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)

# Global data store
RESUME_DATA = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/overview")
def api_overview():
    """Return overview stats for the dashboard hero section."""
    total = len(RESUME_DATA)
    resumes_only = [r for r in RESUME_DATA if r["doc_type"] == "Resume"]
    covers_only = [r for r in RESUME_DATA if r["doc_type"] == "Cover Letter"]

    # Best resume per role
    best_per_role = {}
    for role in ALL_ROLES:
        ranked = sorted(RESUME_DATA, key=lambda r: r["role_analyses"][role]["score"], reverse=True)
        if ranked:
            best = ranked[0]
            best_per_role[role] = {
                "filename": best["filename"],
                "score": best["role_analyses"][role]["score"],
                "label": best["role_analyses"][role]["label"],
                "coverage": best["role_analyses"][role]["keywords"]["coverage_pct"],
            }

    # Overall avg score
    avg_scores = {}
    for role in ALL_ROLES:
        scores = [r["role_analyses"][role]["score"] for r in resumes_only]
        avg_scores[role] = round(sum(scores) / max(len(scores), 1), 1) if scores else 0

    return jsonify({
        "total_resumes": len(resumes_only),
        "total_cover_letters": len(covers_only),
        "total_files": total,
        "roles": ALL_ROLES,
        "best_per_role": best_per_role,
        "avg_scores": avg_scores,
    })


@app.route("/api/resumes")
def api_resumes():
    """Return list of all resumes with summary data."""
    result = []
    for r in RESUME_DATA:
        summary = {
            "id": r["id"],
            "filename": r["filename"],
            "path": r["path"],
            "extension": r["extension"],
            "size_kb": r["size_kb"],
            "modified": r["modified"],
            "doc_type": r["doc_type"],
            "companies": r["companies"],
            "best_role": r["best_role"],
            "best_score": r["best_score"],
            "word_count": r["word_count"],
            "role_scores": {role: r["role_analyses"][role]["score"] for role in ALL_ROLES},
        }
        result.append(summary)
    return jsonify(result)


@app.route("/api/resume/<int:resume_id>")
def api_resume_detail(resume_id):
    """Return full analysis for a specific resume across all 4 roles."""
    if resume_id < 0 or resume_id >= len(RESUME_DATA):
        return jsonify({"error": "Resume not found"}), 404
    return jsonify(RESUME_DATA[resume_id])


@app.route("/api/role/<path:role_name>")
def api_role_rankings(role_name):
    """Return all resumes ranked for a specific role."""
    if role_name not in ROLE_KEYWORDS:
        return jsonify({"error": f"Unknown role: {role_name}"}), 404

    ranked = []
    for r in RESUME_DATA:
        analysis = r["role_analyses"][role_name]
        ranked.append({
            "id": r["id"],
            "filename": r["filename"],
            "doc_type": r["doc_type"],
            "score": analysis["score"],
            "label": analysis["label"],
            "coverage": analysis["keywords"]["coverage_pct"],
            "found": analysis["keywords"]["total_found"],
            "total": analysis["keywords"]["total_keywords"],
            "breakdown": analysis["breakdown"],
            "tips_count": len(analysis["tips"]),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({
        "role": role_name,
        "keywords": ROLE_KEYWORDS[role_name],
        "resumes": ranked,
    })


@app.route("/api/keyword-matrix")
def api_keyword_matrix():
    """Return the keyword gap matrix data for all roles and resumes."""
    resumes_only = [r for r in RESUME_DATA if r["doc_type"] == "Resume"]
    matrix = {}

    for role in ALL_ROLES:
        role_data = {"categories": {}}
        for category, keywords in ROLE_KEYWORDS[role].items():
            cat_data = []
            for kw in keywords:
                row = {"keyword": kw, "resumes": {}}
                for resume in resumes_only:
                    analysis = resume["role_analyses"][role]["keywords"]["categories"][category]
                    kw_entry = next((k for k in analysis if k["keyword"] == kw), None)
                    row["resumes"][resume["filename"]] = kw_entry["found"] if kw_entry else False
                cat_data.append(row)
            role_data["categories"][category] = cat_data
        matrix[role] = role_data

    resume_names = [r["filename"] for r in resumes_only]
    return jsonify({"matrix": matrix, "resume_names": resume_names})


# ═══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n  Resume Intelligence Dashboard")
    print("  Loading and analyzing resumes...\n")
    RESUME_DATA = load_and_analyze()
    print(f"\n  Starting dashboard at http://localhost:5000\n")
    app.run(debug=False, port=5000)

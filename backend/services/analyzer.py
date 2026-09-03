"""
Resume analysis engine — ported from legacy/dashboard.py.

Pure functions for scoring, keyword analysis, company detection, and tip generation.
No web framework dependencies.
"""

import re
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════════════════
# ROLE DEFINITIONS — Expert HM keyword sets for 4 target roles
# ═══════════════════════════════════════════════════════════════════════════════

ROLE_KEYWORDS: dict[str, dict[str, list[str]]] = {
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

# Known companies to detect in resume content
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
    "BWC",
]


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def detect_companies(text: str, filename: str = "") -> list[str]:
    """Find company names mentioned in the resume."""
    combined = text + " " + filename
    found = set()
    for company in KNOWN_COMPANIES:
        pattern = re.compile(r'\b' + re.escape(company) + r'\b', re.IGNORECASE)
        if pattern.search(combined):
            found.add(company)
    return sorted(found)


def analyze_keywords_for_role(text: str, role: str) -> dict:
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


def score_resume_for_role(text: str, role: str) -> tuple[int, str, dict]:
    """
    Score a resume 0-100 for a specific role as an expert HM.

    Returns: (score, label, breakdown_dict)
    """
    if not text or len(text.strip()) < 50:
        return 10, "Unable to extract content", {}

    text_lower = text.lower()
    score = 0
    breakdown = {}

    # 1. Keyword coverage (0-30)
    role_kws = ROLE_KEYWORDS.get(role, {})
    all_kws = [kw for cat in role_kws.values() for kw in cat]
    hits = sum(1 for kw in all_kws if kw in text_lower)
    kw_ratio = hits / max(len(all_kws), 1)
    kw_score = min(int(kw_ratio * 60), 30)
    score += kw_score
    breakdown["Keyword Coverage"] = {
        "score": kw_score, "max": 30,
        "detail": f"{hits}/{len(all_kws)} keywords found",
    }

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
    breakdown["Quantified Impact"] = {
        "score": metrics_score, "max": 20,
        "detail": f"{metric_hits} metric patterns found",
    }

    # 3. Structure (0-15)
    structure_signals = [
        "experience", "education", "skills", "projects", "summary",
        "objective", "work history", "technical skills", "achievements",
        "certifications", "awards", "publications", "volunteer",
    ]
    struct_hits = sum(1 for s in structure_signals if s in text_lower)
    struct_score = min(struct_hits * 3, 15)
    score += struct_score
    breakdown["Resume Structure"] = {
        "score": struct_score, "max": 15,
        "detail": f"{struct_hits} sections detected",
    }

    # 4. Education (0-15)
    edu_signals = [
        "bachelor", "master", "mba", "phd", "b.sc", "m.sc", "b.eng", "m.eng",
        "university", "college", "degree", "gpa", "dean's list", "honors",
        "certification", "certified", "aws certified", "pmp",
    ]
    edu_hits = sum(1 for e in edu_signals if e in text_lower)
    edu_score = min(edu_hits * 3, 15)
    score += edu_score
    breakdown["Education & Credentials"] = {
        "score": edu_score, "max": 15,
        "detail": f"{edu_hits} education signals",
    }

    # 5. Experience depth (0-10)
    date_ranges = len(re.findall(r'20\d{2}\s*[-\u2013]\s*(20\d{2}|present|current)', text_lower))
    exp_score = min(date_ranges * 3, 10)
    score += exp_score
    breakdown["Experience Depth"] = {
        "score": exp_score, "max": 10,
        "detail": f"{date_ranges} role date ranges",
    }

    # 6. Professional presentation (0-10)
    pro_signals = ["linkedin", "github", "portfolio", "email", "phone"]
    pro_hits = sum(1 for p in pro_signals if p in text_lower)
    pro_score = min(pro_hits * 2, 10)
    score += pro_score
    breakdown["Professional Presentation"] = {
        "score": pro_score, "max": 10,
        "detail": f"{pro_hits}/5 contact elements",
    }

    score = min(score, 100)

    # Penalize short content
    word_count = len(text.split())
    if word_count < 100:
        score = min(score, 35)
    elif word_count < 200:
        score = max(score - 10, 0)

    return score, _score_label(score), breakdown


def _score_label(score: int) -> str:
    if score >= 80: return "Excellent"
    if score >= 65: return "Strong"
    if score >= 50: return "Good"
    if score >= 35: return "Needs Work"
    return "Weak"


def generate_tips(text: str, role: str, keyword_analysis: dict) -> list[dict]:
    """Generate actionable resume improvement tips for a specific role."""
    tips = []
    text_lower = text.lower() if text else ""

    # Missing keywords by category
    for category, keywords in keyword_analysis["categories"].items():
        missing = [kw["keyword"] for kw in keywords if not kw["found"]]
        found_list = [kw["keyword"] for kw in keywords if kw["found"]]
        if missing and len(missing) > len(found_list):
            tips.append({
                "type": "keyword_gap",
                "severity": "high" if len(missing) > len(found_list) * 2 else "medium",
                "category": category,
                "title": f"Add more {category} keywords",
                "description": f"Your resume is missing key {category.lower()} terms that hiring managers for {role} look for.",
                "keywords": missing[:5],
            })
        elif missing:
            tips.append({
                "type": "keyword_gap",
                "severity": "low",
                "category": category,
                "title": f"Consider adding {category} keywords",
                "description": f"A few {category.lower()} terms could strengthen your {role} application.",
                "keywords": missing[:3],
            })

    # Quantified metrics check
    metric_hits = sum(1 for p in [r'\d+%', r'\$[\d,]+', r'\d+x\b']
                      if re.search(p, text_lower))
    if metric_hits < 3:
        tips.append({
            "type": "metrics",
            "severity": "high",
            "category": "Impact",
            "title": "Add more quantified achievements",
            "description": "Hiring managers love numbers. Quantify your impact: "
                           "'Reduced build time by 40%', 'Served 10K+ users', 'Managed team of 5'.",
            "keywords": [],
        })

    # Action verbs
    strong_verbs = ["architected", "spearheaded", "engineered", "orchestrated", "streamlined"]
    used_strong = [v for v in strong_verbs if v in text_lower]
    if len(used_strong) < 2:
        tips.append({
            "type": "language",
            "severity": "medium",
            "category": "Language",
            "title": "Use stronger action verbs",
            "description": "Replace generic verbs like 'worked on' with power verbs.",
            "keywords": ["Architected", "Spearheaded", "Engineered", "Orchestrated", "Streamlined"],
        })

    # Professional presence
    if "linkedin" not in text_lower:
        tips.append({
            "type": "presentation", "severity": "medium", "category": "Presentation",
            "title": "Add your LinkedIn URL",
            "description": "Most hiring managers check LinkedIn. Include your profile URL.",
            "keywords": [],
        })
    if "github" not in text_lower and role in ("Software Engineer", "Full Stack Developer"):
        tips.append({
            "type": "presentation", "severity": "medium", "category": "Presentation",
            "title": "Add your GitHub profile",
            "description": f"For {role} roles, a GitHub link with active projects boosts credibility.",
            "keywords": [],
        })

    return tips


def analyze_resume_for_all_roles(text: str, filename: str = "") -> dict:
    """Run full analysis of a resume against all 4 target roles. Returns a dict keyed by role."""
    companies = detect_companies(text, filename)
    results = {}

    for role in ALL_ROLES:
        kw_analysis = analyze_keywords_for_role(text, role)
        score, label, breakdown = score_resume_for_role(text, role)
        tips = generate_tips(text, role, kw_analysis)

        results[role] = {
            "score": score,
            "label": label,
            "breakdown": breakdown,
            "keywords": kw_analysis,
            "tips": tips,
        }

    best_role = max(ALL_ROLES, key=lambda r: results[r]["score"])

    return {
        "companies": companies,
        "best_role": best_role,
        "best_score": results[best_role]["score"],
        "role_analyses": results,
    }

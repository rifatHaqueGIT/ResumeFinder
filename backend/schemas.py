"""
Pydantic schemas for API request/response serialization.
"""

from pydantic import BaseModel


# ── Resume Schemas ──────────────────────────────────────────────────

class ResumeSummary(BaseModel):
    """Lightweight resume info for list views."""
    id: int
    filename: str
    extension: str
    size_kb: float
    modified_at: str | None = None
    doc_type: str
    companies: list[str] = []
    best_role: str | None = None
    best_score: int | None = None
    word_count: int = 0
    role_scores: dict[str, int] = {}

    class Config:
        from_attributes = True


class KeywordResult(BaseModel):
    keyword: str
    found: bool


class KeywordCategory(BaseModel):
    category: str
    keywords: list[KeywordResult]


class ScoreBreakdown(BaseModel):
    score: int
    max: int
    detail: str


class TipSchema(BaseModel):
    type: str
    severity: str
    category: str
    title: str
    description: str
    keywords: list[str] = []


class RoleAnalysis(BaseModel):
    """Full analysis of a resume for one role."""
    role_name: str
    score: int
    label: str
    breakdown: dict[str, ScoreBreakdown] = {}
    keywords: dict  # Full keyword analysis structure
    coverage_pct: float
    tips: list[TipSchema] = []


class ResumeDetail(BaseModel):
    """Full resume with analysis for all roles."""
    id: int
    filename: str
    filepath: str
    folder: str | None = None
    extension: str
    size_kb: float
    modified_at: str | None = None
    doc_type: str
    companies: list[str] = []
    best_role: str | None = None
    best_score: int | None = None
    word_count: int = 0
    role_analyses: dict[str, RoleAnalysis] = {}

    class Config:
        from_attributes = True


# ── Role Schemas ────────────────────────────────────────────────────

class RoleRanking(BaseModel):
    """A resume ranked for a specific role."""
    id: int
    filename: str
    doc_type: str
    score: int
    label: str
    coverage: float
    found: int
    total: int
    tips_count: int = 0


class RoleDetail(BaseModel):
    """Full role info with keyword definitions and resume rankings."""
    role: str
    keywords: dict[str, list[str]]
    resumes: list[RoleRanking]


# ── Overview Schema ─────────────────────────────────────────────────

class BestPerRole(BaseModel):
    filename: str
    score: int
    label: str
    coverage: float


class OverviewResponse(BaseModel):
    total_resumes: int
    total_cover_letters: int
    total_files: int
    roles: list[str]
    best_per_role: dict[str, BestPerRole]
    avg_scores: dict[str, float]


# ── Keyword Matrix ──────────────────────────────────────────────────

class MatrixKeyword(BaseModel):
    keyword: str
    resumes: dict[str, bool]


class MatrixCategory(BaseModel):
    category: str
    keywords: list[MatrixKeyword]


class MatrixResponse(BaseModel):
    matrix: dict[str, dict[str, list[MatrixKeyword]]]
    resume_names: list[str]

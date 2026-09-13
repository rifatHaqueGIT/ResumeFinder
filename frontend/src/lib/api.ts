/**
 * API client — fetches data from the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

// ── Types ──────────────────────────────────────────────────────────

export interface ResumeSummary {
  id: number;
  filename: string;
  extension: string;
  size_kb: number;
  modified_at: string | null;
  doc_type: string;
  companies: string[];
  best_role: string | null;
  best_score: number | null;
  word_count: number;
  role_scores: Record<string, number>;
}

export interface ScoreBreakdown {
  score: number;
  max: number;
  detail: string;
}

export interface KeywordResult {
  keyword: string;
  found: boolean;
}

export interface KeywordAnalysis {
  categories: Record<string, KeywordResult[]>;
  total_found: number;
  total_keywords: number;
  coverage_pct: number;
}

export interface Tip {
  type: string;
  severity: string;
  category: string;
  title: string;
  description: string;
  keywords: string[];
}

export interface RoleAnalysis {
  score: number;
  label: string;
  breakdown: Record<string, ScoreBreakdown>;
  keywords: KeywordAnalysis;
  coverage_pct: number;
  tips: Tip[];
}

export interface ResumeDetail {
  id: number;
  filename: string;
  filepath: string;
  folder: string | null;
  extension: string;
  size_kb: number;
  modified_at: string | null;
  doc_type: string;
  companies: string[];
  best_role: string | null;
  best_score: number | null;
  word_count: number;
  role_analyses: Record<string, RoleAnalysis>;
}

export interface BestPerRole {
  filename: string;
  score: number;
  label: string;
  coverage: number;
}

export interface OverviewData {
  total_resumes: number;
  total_cover_letters: number;
  total_files: number;
  roles: string[];
  best_per_role: Record<string, BestPerRole>;
  avg_scores: Record<string, number>;
}

export interface RoleRanking {
  id: number;
  filename: string;
  doc_type: string;
  score: number;
  label: string;
  coverage: number;
  found: number;
  total: number;
  tips_count: number;
}

export interface RoleDetail {
  role: string;
  keywords: Record<string, string[]>;
  resumes: RoleRanking[];
}

export interface MatrixKeyword {
  keyword: string;
  resumes: Record<string, boolean>;
}

export interface MatrixData {
  matrix: Record<string, { categories: Record<string, MatrixKeyword[]> }>;
  resume_names: string[];
}

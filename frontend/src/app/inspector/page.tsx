"use client";

import { useEffect, useState } from "react";
import { fetchAPI, ResumeSummary, ResumeDetail, OverviewData } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import { getScoreClass } from "@/components/ScoreGauge";
import KeywordPill from "@/components/KeywordPill";

export default function InspectorPage() {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ResumeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAPI<ResumeSummary[]>("/api/resumes"),
      fetchAPI<OverviewData>("/api/overview"),
    ]).then(([r, o]) => {
      setResumes(r);
      setRoles(o.roles);
      if (r.length > 0) setSelectedId(r[0].id);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (selectedId === null) return;
    fetchAPI<ResumeDetail>(`/api/resumes/${selectedId}`).then(setDetail);
  }, [selectedId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-10 h-10 border-3 border-border border-t-accent-cyan rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="text-[28px] font-extrabold gradient-text mb-1">Resume Inspector</h1>
        <p className="text-text-secondary text-sm">Select a resume to see its fit across all 4 roles</p>
      </div>

      {/* Resume Chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {resumes.map((r) => (
          <button
            key={r.id}
            onClick={() => setSelectedId(r.id)}
            className={`px-4 py-2 rounded-lg text-xs font-medium border transition-all duration-200 cursor-pointer ${
              selectedId === r.id
                ? "bg-accent-purple/15 border-accent-purple/30 text-accent-purple"
                : "bg-bg-glass border-border text-text-secondary hover:bg-bg-glass-hover hover:text-text-primary"
            }`}
            title={r.filename}
          >
            {r.filename.length > 22 ? r.filename.slice(0, 19) + "..." : r.filename}
          </button>
        ))}
      </div>

      {/* Detail */}
      {detail && (
        <div>
          {/* Resume info header */}
          <div className="mb-6">
            <h2 className="text-lg font-bold text-text-bright mb-1">{detail.filename}</h2>
            <p className="text-xs text-text-secondary">
              {detail.doc_type} · {detail.word_count} words · {detail.size_kb} KB · Modified: {detail.modified_at}
              {detail.companies.length > 0 && ` · Companies: ${detail.companies.join(", ")}`}
            </p>
          </div>

          {/* Role comparison grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {roles.map((role) => {
              const analysis = detail.role_analyses[role];
              if (!analysis) return null;
              const isBest = role === detail.best_role;

              return (
                <div
                  key={role}
                  className={`bg-bg-card border rounded-xl p-5 transition-all duration-200 hover:border-border-hover ${
                    isBest ? "border-accent-cyan/30" : "border-border"
                  }`}
                >
                  <h3 className="text-sm font-bold text-accent-cyan mb-4">
                    {role}{" "}
                    {isBest && (
                      <span className="text-[10px] text-score-high ml-1">★ BEST FIT</span>
                    )}
                  </h3>

                  {/* Score */}
                  <div className="flex items-center gap-4 mb-4">
                    <ScoreGauge score={analysis.score} size={64} />
                    <div>
                      <div className={`text-base font-semibold ${getScoreClass(analysis.score)}`}>
                        {analysis.label}
                      </div>
                      <div className="text-xs text-text-secondary">
                        {analysis.keywords.coverage_pct}% keywords
                      </div>
                    </div>
                  </div>

                  {/* Breakdown bars */}
                  <div className="flex flex-col gap-2.5 mb-4">
                    {Object.entries(analysis.breakdown).map(([name, b]) => (
                      <div key={name} className="flex items-center text-xs">
                        <span className="text-text-secondary w-[140px] shrink-0 truncate">{name}</span>
                        <div className="flex-1 h-1.5 bg-white/5 rounded-full mx-3 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-accent-cyan to-accent-purple transition-all duration-700"
                            style={{ width: `${(b.score / b.max) * 100}%` }}
                          />
                        </div>
                        <span className="font-semibold text-text-primary min-w-[40px] text-right">
                          {b.score}/{b.max}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Keywords */}
                  {Object.entries(analysis.keywords.categories).map(([cat, kws]) => (
                    <div key={cat} className="mb-2">
                      <div className="text-[11px] text-accent-cyan font-semibold uppercase mb-1">
                        {cat}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {kws.map((k) => (
                          <KeywordPill key={k.keyword} keyword={k.keyword} found={k.found} />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

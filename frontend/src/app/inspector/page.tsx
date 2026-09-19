"use client";

import { useEffect, useState } from "react";
import { fetchAPI, ResumeListItem, ResumeDetail } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import KeywordPill from "@/components/KeywordPill";

export default function InspectorPage() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [selected, setSelected] = useState<ResumeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<ResumeListItem[]>("/api/resumes").then((data) => {
      setResumes(data);
      if (data.length > 0) selectResume(data[0].id);
    }).finally(() => setLoading(false));
  }, []);

  const selectResume = (id: number) => {
    fetchAPI<ResumeDetail>(`/api/resumes/${id}`).then(setSelected);
  };

  if (loading) return <Loader />;

  return (
    <div className="animate-fade-in flex gap-4 h-[calc(100vh-48px)]">
      {/* Left: file list */}
      <div className="w-[260px] shrink-0 bg-surface-raised border border-border-default rounded-[6px] overflow-hidden flex flex-col">
        <div className="px-3 py-2.5 border-b border-border-default text-[11px] font-semibold text-text-muted uppercase tracking-wide">
          {resumes.length} Files
        </div>
        <div className="flex-1 overflow-y-auto">
          {resumes.map((r) => (
            <div
              key={r.id}
              onClick={() => selectResume(r.id)}
              className={`px-3 py-2 cursor-pointer border-b border-border-default transition-colors ${
                selected?.id === r.id
                  ? "bg-primary-subtle border-l-2 border-l-primary"
                  : "hover:bg-surface-overlay border-l-2 border-l-transparent"
              }`}
            >
              <div className="text-[12px] font-medium text-text-bright truncate">{r.filename}</div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`text-[10px] font-medium ${
                  r.doc_type === "Resume" ? "text-primary" : "text-warning"
                }`}>{r.doc_type}</span>
                <span className="text-[10px] text-text-muted">{r.best_score}/100</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right: detail */}
      <div className="flex-1 overflow-y-auto">
        {selected ? (
          <div>
            <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">{selected.filename}</h1>
            <p className="text-[13px] text-text-secondary mb-5">
              {selected.doc_type} &middot; {selected.word_count} words &middot; {selected.extension.toUpperCase()} &middot; {selected.size_kb.toFixed(1)} KB
            </p>

            {/* Meta row */}
            <div className="grid grid-cols-3 gap-3 mb-6">
              <div className="bg-surface-raised border border-border-default rounded-[6px] px-4 py-3">
                <div className="text-[11px] text-text-muted uppercase tracking-wide mb-0.5">Best Role</div>
                <div className="text-[14px] font-semibold text-text-bright">{selected.best_role || "N/A"}</div>
              </div>
              <div className="bg-surface-raised border border-border-default rounded-[6px] px-4 py-3">
                <div className="text-[11px] text-text-muted uppercase tracking-wide mb-0.5">Best Score</div>
                <div className="text-[14px] font-semibold text-text-bright">{selected.best_score || 0}/100</div>
              </div>
              <div className="bg-surface-raised border border-border-default rounded-[6px] px-4 py-3">
                <div className="text-[11px] text-text-muted uppercase tracking-wide mb-0.5">Companies</div>
                <div className="text-[14px] font-semibold text-text-bright">{selected.companies?.length || 0}</div>
              </div>
            </div>

            {/* Role analyses */}
            <h2 className="text-[13px] font-semibold text-text-secondary uppercase tracking-wide mb-3">
              Role Analysis Breakdown
            </h2>
            <div className="space-y-3">
              {Object.entries(selected.role_analyses || {}).map(([roleName, analysis]) => (
                <div
                  key={roleName}
                  className="bg-surface-raised border border-border-default rounded-[6px] p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-[13px] font-semibold text-text-bright">{roleName}</h3>
                    <div className="flex items-center gap-3">
                      <ScoreGauge score={analysis.score} size={38} />
                      <span className="text-[12px] text-text-secondary">{analysis.coverage_pct}% coverage</span>
                    </div>
                  </div>

                  {analysis.breakdown && (
                    <div className="space-y-2 mb-3">
                      {Object.entries(analysis.breakdown).map(([cat, val]) => {
                        const pct = typeof val === 'object' && val !== null
                          ? Math.round(((val as {score: number; max: number}).score / (val as {score: number; max: number}).max) * 100)
                          : (typeof val === 'number' ? val : 0);
                        return (
                          <div key={cat} className="flex items-center gap-2">
                            <span className="text-[11px] text-text-secondary w-40 truncate">{cat}</span>
                            <div className="flex-1 h-1.5 bg-surface-overlay rounded-full overflow-hidden">
                              <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(pct, 100)}%` }} />
                            </div>
                            <span className="text-[10px] text-text-muted w-8 text-right">{pct}%</span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {analysis.keywords?.categories && (
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(analysis.keywords.categories).map(([, keywords]) =>
                        (keywords as Array<{keyword: string; found: boolean}>).map((k) => (
                          <KeywordPill key={k.keyword} keyword={k.keyword} found={k.found} />
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-text-secondary text-[13px]">
            Select a file to inspect
          </div>
        )}
      </div>
    </div>
  );
}

function Loader() {
  return (
    <div className="flex items-center justify-center h-[50vh]">
      <div className="w-5 h-5 border-2 border-border-default border-t-primary rounded-full animate-spin" />
    </div>
  );
}

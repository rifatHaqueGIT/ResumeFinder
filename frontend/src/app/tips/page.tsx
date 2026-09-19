"use client";

import { useEffect, useState } from "react";
import { fetchAPI, ResumeListItem, ResumeDetail, Tip } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";

export default function TipsPage() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [selected, setSelected] = useState<ResumeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<ResumeListItem[]>("/api/resumes").then((data) => {
      const resumesOnly = data.filter((r) => r.doc_type === "Resume");
      setResumes(resumesOnly);
      if (resumesOnly.length > 0) selectResume(resumesOnly[0].id);
    }).finally(() => setLoading(false));
  }, []);

  const selectResume = (id: number) => {
    fetchAPI<ResumeDetail>(`/api/resumes/${id}`).then(setSelected);
  };

  if (loading) return <Loader />;

  const severityColor = (severity: string) => {
    if (severity === "high") return "text-negative";
    if (severity === "medium") return "text-warning";
    return "text-primary";
  };

  return (
    <div className="animate-fade-in">
      <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">Resume Tips</h1>
      <p className="text-[13px] text-text-secondary mb-5">Improvement suggestions for each resume by role</p>

      {/* Resume selector */}
      <select
        value={selected?.id ?? ""}
        onChange={(e) => selectResume(Number(e.target.value))}
        className="appearance-none bg-surface-raised border border-border-default rounded-[6px] px-3 py-2 text-[13px] text-text-bright w-full max-w-md mb-6 focus:outline-none focus:border-primary"
      >
        {resumes.map((r) => (
          <option key={r.id} value={r.id}>{r.filename} — Score: {r.best_score}</option>
        ))}
      </select>

      {selected && Object.entries(selected.role_analyses || {}).map(([roleName, analysis]) => {
        const tips: Tip[] = analysis.tips || [];
        if (tips.length === 0) return null;

        return (
          <div key={roleName} className="mb-4 bg-surface-raised border border-border-default rounded-[6px] p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[13px] font-semibold text-text-bright">{roleName}</h2>
              <div className="flex items-center gap-2">
                <ScoreGauge score={analysis.score} size={32} />
                <span className="text-[11px] text-text-muted">{tips.length} tips</span>
              </div>
            </div>
            <div className="space-y-2">
              {tips.map((tip, i) => (
                <div key={i} className="flex items-start gap-3 py-2 border-b border-border-default last:border-0">
                  <span className={`text-[10px] font-semibold uppercase tracking-wide w-16 shrink-0 pt-0.5 ${severityColor(tip.severity)}`}>
                    {tip.severity}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] font-medium text-text-bright">{tip.title}</div>
                    <div className="text-[11px] text-text-secondary leading-relaxed mt-0.5">{tip.description}</div>
                    {tip.keywords && tip.keywords.length > 0 && (
                      <div className="text-[10px] text-text-muted mt-1">
                        Missing: {tip.keywords.join(", ")}
                      </div>
                    )}
                  </div>
                  <span className="text-[10px] text-text-muted px-1.5 py-0.5 border border-border-default rounded shrink-0">
                    {tip.category}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
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

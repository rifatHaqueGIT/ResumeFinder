"use client";

import { useEffect, useState } from "react";
import { fetchAPI, ResumeSummary, ResumeDetail, OverviewData, Tip } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";

export default function TipsPage() {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [tips, setTips] = useState<Tip[]>([]);
  const [analysis, setAnalysis] = useState<{ score: number; label: string; coverage_pct: number } | null>(null);
  const [resumeName, setResumeName] = useState("");

  useEffect(() => {
    Promise.all([
      fetchAPI<ResumeSummary[]>("/api/resumes"),
      fetchAPI<OverviewData>("/api/overview"),
    ]).then(([r, o]) => {
      setResumes(r);
      setRoles(o.roles);
    });
  }, []);

  useEffect(() => {
    if (!selectedResumeId || !selectedRole) return;
    fetchAPI<ResumeDetail>(`/api/resumes/${selectedResumeId}`).then((d) => {
      const roleAnalysis = d.role_analyses[selectedRole];
      if (roleAnalysis) {
        setTips(roleAnalysis.tips);
        setAnalysis({
          score: roleAnalysis.score,
          label: roleAnalysis.label,
          coverage_pct: roleAnalysis.keywords.coverage_pct,
        });
        setResumeName(d.filename);
      }
    });
  }, [selectedResumeId, selectedRole]);

  const severityColor = (s: string) => {
    if (s === "high") return "border-l-score-low";
    if (s === "medium") return "border-l-score-medium";
    return "border-l-score-high";
  };

  const badgeClass = (s: string) => {
    if (s === "high") return "bg-score-low/15 text-score-low";
    if (s === "medium") return "bg-score-medium/15 text-score-medium";
    return "bg-score-high/15 text-score-high";
  };

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="text-[28px] font-extrabold gradient-text mb-1">Resume Builder Tips</h1>
        <p className="text-text-secondary text-sm">
          Actionable advice to strengthen your resume for each target role
        </p>
      </div>

      {/* Selectors */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={selectedResumeId}
          onChange={(e) => setSelectedResumeId(e.target.value)}
          className="px-4 py-2.5 rounded-lg bg-bg-card border border-border text-text-primary text-[13px] min-w-[260px] cursor-pointer focus:outline-none focus:border-accent-cyan appearance-none"
        >
          <option value="">Select a resume...</option>
          {resumes.map((r) => (
            <option key={r.id} value={r.id}>
              {r.filename}
            </option>
          ))}
        </select>

        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          className="px-4 py-2.5 rounded-lg bg-bg-card border border-border text-text-primary text-[13px] min-w-[260px] cursor-pointer focus:outline-none focus:border-accent-cyan appearance-none"
        >
          <option value="">Select a role...</option>
          {roles.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {/* Score summary */}
      {analysis && (
        <div className="flex items-center gap-5 mb-6 p-4 bg-bg-card border border-border rounded-xl">
          <ScoreGauge score={analysis.score} size={64} />
          <div>
            <div className="text-base font-bold text-text-bright">{resumeName}</div>
            <div className="text-[13px] text-text-secondary">
              {analysis.label} fit for{" "}
              <strong className="text-accent-cyan">{selectedRole}</strong> ·{" "}
              {analysis.coverage_pct}% keyword coverage · {tips.length} improvement tips
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      {!selectedResumeId || !selectedRole ? (
        <div className="text-center py-16 text-text-muted text-sm">
          Select a resume and a role to see tips
        </div>
      ) : tips.length === 0 ? (
        <div className="text-center py-16 text-text-muted text-sm">
          No specific tips — this resume is well-optimized for {selectedRole}!
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {tips.map((tip, i) => (
            <div
              key={i}
              className={`bg-bg-card border border-border rounded-xl p-5 border-l-[3px] ${severityColor(tip.severity)} hover:bg-bg-card-hover transition-all duration-200`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${badgeClass(tip.severity)}`}
                >
                  {tip.severity}
                </span>
                <span className="text-sm font-semibold text-text-bright">{tip.title}</span>
              </div>
              <p className="text-[13px] text-text-secondary leading-relaxed mb-2.5">
                {tip.description}
              </p>
              {tip.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {tip.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-accent-purple/12 text-accent-purple border border-accent-purple/20"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

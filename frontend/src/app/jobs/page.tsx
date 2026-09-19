"use client";

import { useState } from "react";
import { fetchAPI } from "@/lib/api";

interface MatchResult {
  analysis: string;
  best_resumes: Array<{ filename: string; doc_type: string; avg_relevance: number; chunk_count: number }>;
  sources: Array<{ filename: string; relevance: number; excerpt: string }>;
}

export default function JobsPage() {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const submitMatch = async () => {
    if (!description.trim() || loading) return;
    setLoading(true);
    setResult(null);

    try {
      const res = await fetchAPI<MatchResult>("/api/jobs/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, company, description }),
      });
      setResult(res);
    } catch {
      setResult({
        analysis: "Failed to analyze. Is Ollama running?",
        best_resumes: [],
        sources: [],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">Job Match</h1>
      <p className="text-[13px] text-text-secondary mb-5">Paste a job description to find your best-matching resume and get gap analysis</p>

      <div className="grid grid-cols-[400px_1fr] gap-6 items-start">
        {/* Left: input form */}
        <div className="bg-surface-raised border border-border-default rounded-[6px] p-4 space-y-3">
          <div>
            <label className="block text-[11px] text-text-muted uppercase tracking-wide mb-1">Job Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Full Stack Developer"
              className="w-full bg-surface-base border border-border-default rounded-[6px] px-3 py-2 text-[13px] text-text-bright placeholder:text-text-muted focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-[11px] text-text-muted uppercase tracking-wide mb-1">Company</label>
            <input
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g. Shopify"
              className="w-full bg-surface-base border border-border-default rounded-[6px] px-3 py-2 text-[13px] text-text-bright placeholder:text-text-muted focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-[11px] text-text-muted uppercase tracking-wide mb-1">Job Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={10}
              placeholder="Paste the full job description here..."
              className="w-full bg-surface-base border border-border-default rounded-[6px] px-3 py-2 text-[13px] text-text-bright placeholder:text-text-muted focus:outline-none focus:border-primary resize-none leading-relaxed"
            />
          </div>
          <button
            onClick={submitMatch}
            disabled={loading || !description.trim()}
            className="w-full bg-primary hover:bg-primary-hover text-white px-4 py-2.5 rounded-[6px] text-[13px] font-medium transition-colors disabled:opacity-40"
          >
            {loading ? "Analyzing..." : "Analyze Match"}
          </button>
        </div>

        {/* Right: results */}
        <div>
          {loading && (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <div className="w-5 h-5 border-2 border-border-default border-t-primary rounded-full animate-spin mx-auto mb-3" />
                <div className="text-[13px] text-text-secondary">Running AI analysis (this may take 15-30s)...</div>
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-4">
              {/* Best resumes */}
              {result.best_resumes.length > 0 && (
                <div className="bg-surface-raised border border-border-default rounded-[6px] p-4">
                  <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-wide mb-3">Best Matching Resumes</h2>
                  <div className="space-y-2">
                    {result.best_resumes.map((r, i) => (
                      <div key={i} className="flex items-center gap-3 py-1.5 border-b border-border-default last:border-0">
                        <span className="text-[12px] text-text-muted w-4">{i + 1}.</span>
                        <span className="text-[13px] text-text-bright font-medium flex-1 truncate">{r.filename}</span>
                        <div className="flex items-center gap-2 shrink-0">
                          <div className="w-16 h-1.5 bg-surface-overlay rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${r.avg_relevance * 100}%` }}
                            />
                          </div>
                          <span className="text-[11px] text-text-muted w-10 text-right">
                            {(r.avg_relevance * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Analysis */}
              <div className="bg-surface-raised border border-border-default rounded-[6px] p-4">
                <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-wide mb-3">AI Analysis</h2>
                <div className="text-[13px] text-text-secondary leading-relaxed whitespace-pre-wrap">
                  {result.analysis}
                </div>
              </div>

              {/* Sources */}
              {result.sources.length > 0 && (
                <div className="bg-surface-raised border border-border-default rounded-[6px] p-4">
                  <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-wide mb-3">Retrieved Chunks</h2>
                  <div className="space-y-2">
                    {result.sources.map((s, i) => (
                      <div key={i} className="border border-border-default rounded-[6px] p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[12px] font-medium text-text-bright">{s.filename}</span>
                          <span className="text-[10px] text-text-muted ml-auto">{(s.relevance * 100).toFixed(0)}% match</span>
                        </div>
                        <p className="text-[11px] text-text-muted leading-relaxed">{s.excerpt}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!result && !loading && (
            <div className="text-center py-16 text-text-muted text-[13px]">
              Paste a job description and click &quot;Analyze Match&quot; to see results
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

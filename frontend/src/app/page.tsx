"use client";

import { useEffect, useState } from "react";
import { fetchAPI, OverviewData } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import { getScoreTextClass } from "@/components/ScoreGauge";
import Link from "next/link";

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<OverviewData>("/api/overview").then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;
  if (!data) return <p className="text-text-secondary">Failed to load.</p>;

  const avgAll = Object.values(data.avg_scores);
  const overallAvg = avgAll.length ? Math.round(avgAll.reduce((a, b) => a + b, 0) / avgAll.length) : 0;

  return (
    <div className="animate-fade-in">
      <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">Dashboard Overview</h1>
      <p className="text-[13px] text-text-secondary mb-6">
        Analysis of {data.total_files} files across {data.roles.length} target roles
      </p>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-3 mb-8">
        {[
          { value: data.total_resumes, label: "Resumes" },
          { value: data.total_cover_letters, label: "Cover Letters" },
          { value: data.roles.length, label: "Target Roles" },
          { value: overallAvg, label: "Avg Score" },
        ].map((s) => (
          <div key={s.label} className="bg-surface-raised border border-border-default rounded-[6px] px-4 py-3">
            <div className="text-2xl font-bold text-text-bright">{s.value}</div>
            <div className="text-[11px] text-text-muted uppercase tracking-wide mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Best per role */}
      <h2 className="text-[13px] font-semibold text-text-secondary uppercase tracking-wide mb-3">Best Resume Per Role</h2>
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        {data.roles.map((role) => {
          const best = data.best_per_role[role];
          if (!best) return null;
          return (
            <Link href="/roles" key={role}>
              <div className="bg-surface-raised border border-border-default rounded-[6px] p-4 hover:border-border-hover transition-colors cursor-pointer">
                <div className="text-[13px] font-semibold text-text-bright mb-2">{role}</div>
                <div className="text-[12px] text-text-secondary mb-3 truncate">
                  {best.filename}
                </div>
                <div className="flex items-center gap-3">
                  <ScoreGauge score={best.score} size={42} />
                  <div>
                    <div className={`text-[12px] font-semibold ${getScoreTextClass(best.score)}`}>{best.label}</div>
                    <div className="text-[11px] text-text-muted">{best.coverage}% keywords</div>
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function Loader() {
  return (
    <div className="flex items-center justify-center h-[50vh]">
      <div className="w-6 h-6 border-2 border-border-default border-t-primary rounded-full animate-spin" />
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { fetchAPI, OverviewData } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import { getScoreClass } from "@/components/ScoreGauge";
import Link from "next/link";

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<OverviewData>("/api/overview")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-12 h-12 border-3 border-border border-t-accent-cyan rounded-full animate-spin" />
      </div>
    );
  }

  if (!data) return <p className="text-text-secondary">Failed to load data.</p>;

  const avgAll = Object.values(data.avg_scores);
  const overallAvg = avgAll.length
    ? Math.round(avgAll.reduce((a, b) => a + b, 0) / avgAll.length)
    : 0;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-[28px] font-extrabold gradient-text mb-1">Dashboard Overview</h1>
        <p className="text-text-secondary text-sm">
          Expert Hiring Manager analysis of your resumes across {data.roles.length} target roles
        </p>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { value: data.total_resumes, label: "Resumes Found" },
          { value: data.total_cover_letters, label: "Cover Letters" },
          { value: data.roles.length, label: "Target Roles" },
          { value: overallAvg, label: "Avg HM Score" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-bg-card border border-border rounded-xl p-5 backdrop-blur-sm hover:bg-bg-card-hover hover:border-border-hover hover:-translate-y-0.5 transition-all duration-200 hover:shadow-lg"
          >
            <div className="text-3xl font-extrabold gradient-text">{stat.value}</div>
            <div className="text-xs text-text-secondary uppercase tracking-wide mt-1">
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Best Resume Per Role */}
      <h2 className="text-lg font-bold text-text-primary mb-4">Best Resume Per Role</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        {data.roles.map((role) => {
          const best = data.best_per_role[role];
          if (!best) return null;

          return (
            <Link href="/roles" key={role}>
              <div className="bg-bg-card border border-border rounded-xl p-6 backdrop-blur-sm cursor-pointer relative overflow-hidden group hover:bg-bg-card-hover hover:border-border-hover hover:-translate-y-1 transition-all duration-200 hover:shadow-xl">
                {/* Accent top bar */}
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-accent-cyan to-accent-purple opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="text-base font-bold text-text-bright mb-3">{role}</div>
                <div className="text-[13px] text-text-secondary mb-2">
                  Best: <strong className="text-accent-cyan">{best.filename.length > 28 ? best.filename.slice(0, 25) + "..." : best.filename}</strong>
                </div>

                <div className="flex items-center gap-3 mt-4">
                  <ScoreGauge score={best.score} />
                  <div>
                    <div className={`text-[13px] font-semibold ${getScoreClass(best.score)}`}>
                      {best.label}
                    </div>
                    <div className="text-xs text-text-secondary">
                      {best.coverage}% keyword coverage
                    </div>
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

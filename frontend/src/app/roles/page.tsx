"use client";

import { useEffect, useState } from "react";
import { fetchAPI, OverviewData, RoleData } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import KeywordPill from "@/components/KeywordPill";

export default function RolesPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [roleData, setRoleData] = useState<RoleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    fetchAPI<OverviewData>("/api/overview").then((d) => {
      setOverview(d);
      if (d.roles.length > 0) setSelectedRole(d.roles[0]);
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedRole) return;
    setRoleData(null);
    fetchAPI<RoleData>(`/api/role/${encodeURIComponent(selectedRole)}`).then(setRoleData);
  }, [selectedRole]);

  if (loading) return <Loader />;
  if (!overview) return <p className="text-text-secondary">Failed to load.</p>;

  return (
    <div className="animate-fade-in">
      <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">Role Deep-Dive</h1>
      <p className="text-[13px] text-text-secondary mb-5">Select a role to view resume rankings and keyword analysis</p>

      {/* Role tabs */}
      <div className="flex gap-1 mb-6 border-b border-border-default pb-px">
        {overview.roles.map((role) => (
          <button
            key={role}
            onClick={() => setSelectedRole(role)}
            className={`px-3 py-2 text-[13px] font-medium border-b-2 transition-colors -mb-px ${
              selectedRole === role
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            {role}
          </button>
        ))}
      </div>

      {/* Rankings table */}
      {roleData ? (
        <div className="bg-surface-raised border border-border-default rounded-[6px] overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-border-default text-text-muted text-[11px] uppercase tracking-wide">
                <th className="text-left font-medium px-4 py-2.5">#</th>
                <th className="text-left font-medium px-4 py-2.5">Resume</th>
                <th className="text-left font-medium px-4 py-2.5">Type</th>
                <th className="text-left font-medium px-4 py-2.5">Score</th>
                <th className="text-left font-medium px-4 py-2.5">Label</th>
                <th className="text-left font-medium px-4 py-2.5">Coverage</th>
                <th className="text-left font-medium px-4 py-2.5">Keywords</th>
              </tr>
            </thead>
            <tbody>
              {roleData.resumes.map((r, i) => (
                <tr
                  key={r.id}
                  onClick={() => setExpandedId(expandedId === r.id ? null : r.id)}
                  className="border-b border-border-default last:border-0 hover:bg-surface-overlay cursor-pointer transition-colors"
                >
                  <td className="px-4 py-2.5 text-text-muted">{i + 1}</td>
                  <td className="px-4 py-2.5 text-text-bright font-medium truncate max-w-[220px]">{r.filename}</td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium border ${
                      r.doc_type === "Resume"
                        ? "border-primary/20 text-primary bg-primary-subtle"
                        : "border-warning/20 text-warning bg-warning-subtle"
                    }`}>
                      {r.doc_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <ScoreGauge score={r.score} size={36} />
                  </td>
                  <td className="px-4 py-2.5 text-text-secondary">{r.label}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-surface-overlay rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${r.coverage}%` }}
                        />
                      </div>
                      <span className="text-text-muted text-[11px]">{r.coverage}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-text-secondary">{r.found}/{r.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Loader />
      )}

      {/* Keywords breakdown */}
      {roleData && (
        <div className="mt-6">
          <h2 className="text-[13px] font-semibold text-text-secondary uppercase tracking-wide mb-3">
            Keyword Categories for {selectedRole}
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(roleData.keywords).map(([category, keywords]) => (
              <div key={category} className="bg-surface-raised border border-border-default rounded-[6px] p-4">
                <h3 className="text-[12px] font-semibold text-text-bright mb-2">{category}</h3>
                <div className="flex flex-wrap gap-1.5">
                  {keywords.map((kw) => (
                    <KeywordPill key={kw} keyword={kw} found={true} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Loader() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-5 h-5 border-2 border-border-default border-t-primary rounded-full animate-spin" />
    </div>
  );
}

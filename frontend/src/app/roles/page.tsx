"use client";

import { useEffect, useState } from "react";
import { fetchAPI, RoleDetail, OverviewData } from "@/lib/api";
import ScoreGauge from "@/components/ScoreGauge";
import { getScoreClass } from "@/components/ScoreGauge";

export default function RolesPage() {
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [roleData, setRoleData] = useState<RoleDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAPI<OverviewData>("/api/overview").then((d) => {
      setRoles(d.roles);
      if (d.roles.length > 0) {
        setSelectedRole(d.roles[0]);
      }
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedRole) return;
    setLoading(true);
    fetchAPI<RoleDetail>(`/api/role/${encodeURIComponent(selectedRole)}`)
      .then(setRoleData)
      .finally(() => setLoading(false));
  }, [selectedRole]);

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="text-[28px] font-extrabold gradient-text mb-1">Role Deep-Dive</h1>
        <p className="text-text-secondary text-sm">Select a role to see how your resumes stack up</p>
      </div>

      {/* Role Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {roles.map((role) => (
          <button
            key={role}
            onClick={() => setSelectedRole(role)}
            className={`px-5 py-2 rounded-full text-[13px] font-semibold border transition-all duration-200 cursor-pointer ${
              selectedRole === role
                ? "bg-accent-cyan/15 border-accent-cyan/30 text-accent-cyan"
                : "bg-bg-glass border-border text-text-secondary hover:bg-bg-glass-hover hover:text-text-primary"
            }`}
          >
            {role}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-10 h-10 border-3 border-border border-t-accent-cyan rounded-full animate-spin" />
        </div>
      )}

      {!loading && roleData && (
        <div>
          {/* Rankings */}
          <div className="flex flex-col gap-3 mb-8">
            {roleData.resumes.map((r, i) => (
              <div
                key={r.id}
                className="bg-bg-card border border-border rounded-xl px-6 py-5 grid grid-cols-[auto_1fr_auto] gap-5 items-center hover:bg-bg-card-hover hover:border-border-hover transition-all duration-200"
              >
                <div className={`text-xl font-extrabold min-w-[32px] text-center ${i === 0 ? "gradient-text" : "text-text-muted"}`}>
                  #{i + 1}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-bright mb-1">{r.filename}</h3>
                  <div className="text-xs text-text-secondary">
                    {r.doc_type} · {r.coverage}% coverage · {r.found}/{r.total} keywords
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <ScoreGauge score={r.score} size={48} />
                  <span className={`text-[13px] font-semibold ${getScoreClass(r.score)}`}>
                    {r.label}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Keyword Reference */}
          <h3 className="text-base font-bold text-text-primary mb-4">
            Keywords for {roleData.role}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Object.entries(roleData.keywords).map(([category, keywords]) => (
              <div
                key={category}
                className="bg-bg-card border border-border rounded-xl p-4"
              >
                <div className="text-[13px] font-bold text-accent-cyan uppercase tracking-wide mb-3">
                  {category}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {keywords.map((kw) => (
                    <span
                      key={kw}
                      className="px-2.5 py-1 rounded-full text-xs font-medium bg-found-bg text-found border border-found/20"
                    >
                      {kw}
                    </span>
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

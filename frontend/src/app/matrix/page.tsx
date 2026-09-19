"use client";

import { useEffect, useState } from "react";
import { fetchAPI, KeywordMatrixData, OverviewData } from "@/lib/api";

export default function MatrixPage() {
  const [data, setData] = useState<KeywordMatrixData | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAPI<KeywordMatrixData>("/api/keyword-matrix"),
      fetchAPI<OverviewData>("/api/overview"),
    ]).then(([matrix, overview]) => {
      setData(matrix);
      setRoles(overview.roles);
      if (overview.roles.length) setSelectedRole(overview.roles[0]);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;
  if (!data || !data.matrix) return <p className="text-text-secondary">Failed to load.</p>;

  const roleMatrix = data.matrix[selectedRole];
  const resumeNames = data.resume_names?.slice(0, 15) || [];

  return (
    <div className="animate-fade-in">
      <h1 className="text-lg font-semibold text-text-bright tracking-tight mb-1">Keyword Gap Matrix</h1>
      <p className="text-[13px] text-text-secondary mb-5">
        Keyword presence across resumes (showing first 15)
      </p>

      {/* Role tabs */}
      <div className="flex gap-1 mb-6 border-b border-border-default pb-px">
        {roles.map((role) => (
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

      {roleMatrix?.categories &&
        Object.entries(roleMatrix.categories).map(([category, keywords]) => (
          <div key={category} className="mb-6">
            <h2 className="text-[12px] font-semibold text-text-secondary uppercase tracking-wide mb-2">{category}</h2>
            <div className="bg-surface-raised border border-border-default rounded-[6px] overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="border-b border-border-default">
                    <th className="text-left font-medium text-text-muted px-3 py-2 sticky left-0 bg-surface-raised min-w-[120px]">
                      Keyword
                    </th>
                    {resumeNames.map((name) => (
                      <th key={name} className="font-medium text-text-muted px-1 py-2 text-center">
                        <span className="inline-block max-w-[60px] truncate" title={name}>
                          {name.replace(/\.(pdf|docx|txt)$/i, "").slice(0, 8)}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(keywords as Array<{ keyword: string; resumes: Record<string, boolean> }>).map((row) => (
                    <tr key={row.keyword} className="border-b border-border-default last:border-0">
                      <td className="px-3 py-1.5 text-text-bright font-medium sticky left-0 bg-surface-raised">
                        {row.keyword}
                      </td>
                      {resumeNames.map((name) => (
                        <td key={name} className="text-center px-1 py-1.5">
                          <span
                            className={`inline-block w-2.5 h-2.5 rounded-full ${
                              row.resumes?.[name] ? "bg-positive" : "bg-surface-overlay"
                            }`}
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
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

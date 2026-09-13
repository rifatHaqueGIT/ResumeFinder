"use client";

import { useEffect, useState } from "react";
import { fetchAPI, MatrixData, OverviewData } from "@/lib/api";

export default function MatrixPage() {
  const [roles, setRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState("");
  const [matrixData, setMatrixData] = useState<MatrixData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAPI<OverviewData>("/api/overview"),
      fetchAPI<MatrixData>("/api/keyword-matrix"),
    ]).then(([overview, matrix]) => {
      setRoles(overview.roles);
      setMatrixData(matrix);
      if (overview.roles.length) setSelectedRole(overview.roles[0]);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-10 h-10 border-3 border-border border-t-accent-cyan rounded-full animate-spin" />
      </div>
    );
  }

  const roleMatrix = matrixData?.matrix[selectedRole];
  const resumeNames = matrixData?.resume_names || [];

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="text-[28px] font-extrabold gradient-text mb-1">Keyword Gap Matrix</h1>
        <p className="text-text-secondary text-sm">
          Every keyword across all roles vs. all resumes — find your blind spots
        </p>
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

      {/* Matrix Table */}
      {roleMatrix && (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr>
                <th className="bg-bg-secondary text-text-secondary px-3 py-2.5 text-left font-semibold uppercase tracking-wide text-[11px] sticky top-0 z-10 border-b border-border">
                  Category
                </th>
                <th className="bg-bg-secondary text-text-secondary px-3 py-2.5 text-left font-semibold uppercase tracking-wide text-[11px] sticky top-0 z-10 border-b border-border">
                  Keyword
                </th>
                {resumeNames.map((name) => (
                  <th
                    key={name}
                    className="bg-bg-secondary text-text-secondary px-2 py-2.5 text-center font-semibold uppercase tracking-wide text-[10px] sticky top-0 z-10 border-b border-border max-w-[100px] truncate"
                    title={name}
                  >
                    {name.length > 12 ? name.slice(0, 10) + ".." : name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(roleMatrix.categories).map(([category, keywords]) =>
                keywords.map((kw, i) => (
                  <tr key={`${category}-${kw.keyword}`} className="hover:bg-bg-glass-hover transition-colors">
                    {i === 0 && (
                      <td
                        rowSpan={keywords.length}
                        className="px-3 py-2 font-bold text-accent-cyan text-[11px] uppercase align-top border-b border-border"
                      >
                        {category}
                      </td>
                    )}
                    <td className="px-3 py-2 font-medium text-text-primary border-b border-border">
                      {kw.keyword}
                    </td>
                    {resumeNames.map((name) => (
                      <td key={name} className="px-2 py-2 text-center border-b border-border">
                        <span
                          className={`block w-5 h-5 rounded-full mx-auto ${
                            kw.resumes[name]
                              ? "bg-found shadow-[0_0_8px_rgba(34,197,94,0.3)]"
                              : "bg-missing-bg border-2 border-missing/30"
                          }`}
                        />
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

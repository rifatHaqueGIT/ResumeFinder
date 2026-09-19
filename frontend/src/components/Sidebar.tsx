"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview", icon: "M3 3h7v7H3V3zm11 0h7v7h-7V3zM3 14h7v7H3v-7zm11 0h7v7h-7v-7z" },
  { href: "/roles", label: "Role Deep-Dive", icon: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" },
  { href: "/inspector", label: "Resume Inspector", icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8" },
  { href: "/matrix", label: "Keyword Matrix", icon: "M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18" },
  { href: "/tips", label: "Resume Tips", icon: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM12 16v-4M12 8h.01" },
  { href: "/chat", label: "AI Chat", icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" },
  { href: "/jobs", label: "Job Match", icon: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="fixed left-0 top-0 bottom-0 w-[220px] bg-surface-raised border-r border-border-default flex flex-col z-50">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-border-default">
        <div className="w-7 h-7 rounded-[6px] bg-primary flex items-center justify-center text-[10px] font-bold text-white shrink-0">
          RI
        </div>
        <span className="text-[13px] font-semibold text-text-bright">
          Resume Intelligence
        </span>
      </div>

      {/* Nav Links */}
      <ul className="flex flex-col gap-0.5 px-2.5 pt-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-[6px] text-[13px] font-medium transition-colors ${
                  isActive
                    ? "bg-primary-subtle text-primary"
                    : "text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
                }`}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="w-4 h-4 shrink-0">
                  <path d={item.icon} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

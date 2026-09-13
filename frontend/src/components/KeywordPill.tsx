"use client";

interface KeywordPillProps {
  keyword: string;
  found: boolean;
}

export default function KeywordPill({ keyword, found }: KeywordPillProps) {
  return (
    <span
      className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium border transition-transform hover:scale-105 ${
        found
          ? "bg-found-bg text-found border-found/20"
          : "bg-missing-bg text-missing border-missing/20"
      }`}
    >
      {keyword}
    </span>
  );
}

"use client";

interface KeywordPillProps {
  keyword: string;
  found: boolean;
}

export default function KeywordPill({ keyword, found }: KeywordPillProps) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium border ${
        found
          ? "bg-positive-subtle text-positive border-positive/20"
          : "bg-negative-subtle text-negative border-negative/20"
      }`}
    >
      {keyword}
    </span>
  );
}

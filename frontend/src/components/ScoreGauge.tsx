"use client";

export function getScoreColor(score: number): string {
  if (score >= 65) return "var(--color-positive)";
  if (score >= 40) return "var(--color-warning)";
  return "var(--color-negative)";
}

export function getScoreTextClass(score: number): string {
  if (score >= 65) return "text-positive";
  if (score >= 40) return "text-warning";
  return "text-negative";
}

interface ScoreGaugeProps {
  score: number;
  size?: number;
}

export default function ScoreGauge({ score, size = 48 }: ScoreGaugeProps) {
  const strokeWidth = 3;
  const r = (size - strokeWidth * 2) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = getScoreColor(score);

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="var(--color-border-default)" strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          className="score-gauge-fill"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-semibold" style={{ color }}>{score}</span>
      </div>
    </div>
  );
}

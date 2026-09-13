"use client";

export function getScoreColor(score: number): string {
  if (score >= 65) return "var(--color-score-high)";
  if (score >= 40) return "var(--color-score-medium)";
  return "var(--color-score-low)";
}

export function getScoreClass(score: number): string {
  if (score >= 65) return "text-score-high";
  if (score >= 40) return "text-score-medium";
  return "text-score-low";
}

interface ScoreGaugeProps {
  score: number;
  size?: number;
}

export default function ScoreGauge({ score, size = 56 }: ScoreGaugeProps) {
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = getScoreColor(score);

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={4}
        />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={4}
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          className="score-gauge-fill"
        />
      </svg>
      <div
        className={`absolute inset-0 flex items-center justify-center font-bold text-sm ${getScoreClass(score)}`}
      >
        {score}
      </div>
    </div>
  );
}

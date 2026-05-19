export function ConfidenceBar({
  value,
  label = "Confidence",
  hint
}: {
  value: number;
  label?: string;
  hint?: string;
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-[12px] uppercase tracking-wider text-white/60">{label}</span>
        <span className="text-sm font-mono text-white">{pct.toFixed(1)}%</span>
      </div>
      <div className="progress">
        <span style={{ width: `${pct}%` }} />
      </div>
      {hint && <p className="mt-2 text-[11px] text-white/45 leading-relaxed">{hint}</p>}
    </div>
  );
}

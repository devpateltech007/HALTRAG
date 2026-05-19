import type { DetectorSignals } from "@/lib/api";
import { AlertCircle, ScanLine, ShieldCheck, ShieldAlert } from "lucide-react";
import { ConfidenceBar } from "./ConfidenceBar";

const AGREEMENT_BADGE: Record<string, string> = {
  high: "badge-low",
  medium: "badge-medium",
  low: "badge-high"
};

export function DetectorPanel({ signals }: { signals: DetectorSignals }) {
  const tone = AGREEMENT_BADGE[signals.agreement_level] || "badge-medium";
  const disagreement = signals.signal_disagreement;
  return (
    <section className="glass rounded-2xl p-5">
      <header className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
            <ScanLine size={16} className="text-accent-cyan" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white tracking-tight">
              Detector Reliability
            </h3>
            <p className="text-[11px] text-white/45">
              The detector is probabilistic, not an oracle.
            </p>
          </div>
        </div>
        <span className={`badge ${tone}`}>{signals.agreement_level} agreement</span>
      </header>

      <div className="grid md:grid-cols-2 gap-5">
        <ConfidenceBar
          label="Detector confidence"
          value={signals.detector_confidence}
          hint="Aggregated from NLI entailment, semantic similarity, lexical overlap, retrieval strength."
        />
        <div className="space-y-2">
          <span className="label-text">Signal agreement</span>
          <div className="flex items-center gap-2">
            {disagreement ? (
              <>
                <ShieldAlert size={16} className="text-amber-300" />
                <span className="text-sm text-amber-200">
                  Signals disagree — treat answer as uncertain.
                </span>
              </>
            ) : (
              <>
                <ShieldCheck size={16} className="text-emerald-300" />
                <span className="text-sm text-emerald-200">
                  Signals agree across NLI, similarity, overlap, and retrieval.
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="mt-5 p-4 rounded-xl bg-black/30 border border-white/5 text-[13px] leading-relaxed text-white/80">
        <div className="flex items-start gap-2">
          <AlertCircle size={14} className="mt-0.5 text-accent-cyan shrink-0" />
          <p>{signals.explanation}</p>
        </div>
      </div>
    </section>
  );
}

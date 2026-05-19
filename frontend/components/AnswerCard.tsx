import type { QueryResponse } from "@/lib/api";
import { RiskBadge, TypeBadge } from "./Badges";
import { ConfidenceBar } from "./ConfidenceBar";
import { Cpu, Quote } from "lucide-react";

export function AnswerCard({ response }: { response: QueryResponse }) {
  return (
    <section className="glass-strong rounded-2xl p-6 animate-fadeIn">
      <header className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div className="flex items-center gap-2">
          <Quote size={16} className="text-white/50" />
          <h2 className="text-sm uppercase tracking-wider text-white/55 font-semibold">
            Answer
          </h2>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <RiskBadge risk={response.risk} />
          <TypeBadge type={response.hallucination_type} />
          <span className="pill">
            <Cpu size={12} className="text-white/60" />
            <span className="text-white/80">{response.provider}</span>
          </span>
        </div>
      </header>

      <p className="text-[16px] leading-relaxed text-white/95 whitespace-pre-line">
        {response.answer}
      </p>

      <div className="mt-5 grid md:grid-cols-2 gap-5">
        <ConfidenceBar
          value={response.confidence}
          label="Overall confidence"
          hint="Composite of retrieval quality, sentence grounding, detector validation, and signal agreement."
        />
        <ConfidenceBar
          value={response.detector_signals.detector_confidence}
          label="Detector confidence"
          hint="Independent multi-signal hallucination check (NLI + similarity + overlap + retrieval)."
        />
      </div>
    </section>
  );
}

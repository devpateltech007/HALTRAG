"use client";

import { useState } from "react";
import type { SentenceAnalysis } from "@/lib/api";
import { LabelBadge } from "./Badges";
import { ChevronDown, ChevronRight } from "lucide-react";

function ScorePill({ label, value }: { label: string; value: number }) {
  const v = Number.isFinite(value) ? value : 0;
  return (
    <div className="flex flex-col gap-1 min-w-0">
      <span className="text-[10px] uppercase tracking-wider text-white/45">{label}</span>
      <div className="flex items-center gap-2">
        <div className="progress flex-1">
          <span style={{ width: `${Math.max(0, Math.min(1, v)) * 100}%` }} />
        </div>
        <span className="text-[11px] font-mono text-white/70 w-10 text-right">
          {v.toFixed(2)}
        </span>
      </div>
    </div>
  );
}

export function SentenceItem({ item, index }: { item: SentenceAnalysis; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <article className={`sentence-card ${item.label}`}>
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-white/45">#{index + 1}</span>
          <LabelBadge label={item.label} />
        </div>
        <span className="text-[11px] font-mono text-white/65">
          grounding {item.grounding_score.toFixed(2)}
        </span>
      </div>
      <p className="text-[14px] leading-relaxed text-white/90">{item.sentence}</p>

      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
        <ScorePill label="NLI Entailment" value={item.entailment_score} />
        <ScorePill label="Semantic Similarity" value={item.semantic_similarity} />
        <ScorePill label="Lexical Overlap" value={item.overlap_score} />
        <ScorePill label="Contradiction" value={item.contradiction_score} />
      </div>

      {item.best_context && (
        <>
          <button
            onClick={() => setOpen((v) => !v)}
            className="mt-3 text-[12px] text-white/55 hover:text-white inline-flex items-center gap-1"
          >
            {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            {open ? "Hide supporting context" : "Show supporting context"}
          </button>
          {open && (
            <div className="mt-2 text-[13px] leading-relaxed text-white/70 bg-black/30 border border-white/5 rounded-xl p-3 animate-fadeIn">
              {item.best_context}
            </div>
          )}
        </>
      )}
    </article>
  );
}

export function SentenceLegend() {
  return (
    <div className="flex flex-wrap gap-2 text-[11px]">
      <span className="badge badge-low">grounded</span>
      <span className="badge badge-medium">uncertain</span>
      <span className="badge badge-high">hallucinated</span>
    </div>
  );
}

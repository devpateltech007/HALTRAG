"use client";

import { useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ShieldQuestion,
  Layers
} from "lucide-react";
import type { RetrievedSource } from "@/lib/api";

export function SourceCard({ source, index }: { source: RetrievedSource; index: number }) {
  const [open, setOpen] = useState(false);
  const score = Math.max(0, Math.min(1, source.score));
  const meta = source.metadata || {};
  const domain = (meta["domain"] as string) || (meta["source_type"] as string) || "general";

  return (
    <article className="glass rounded-2xl p-4 hover:border-white/15 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="shrink-0 w-7 h-7 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-[11px] font-mono text-white/70">
            {index + 1}
          </span>
          <div className="min-w-0">
            <div className="text-sm font-medium text-white truncate">{source.source_id}</div>
            <div className="text-[11px] text-white/45 flex items-center gap-2 mt-0.5">
              <span className="inline-flex items-center gap-1">
                <Layers size={11} /> {domain}
              </span>
              {source.verified ? (
                <span className="inline-flex items-center gap-1 text-emerald-300/80">
                  <CheckCircle2 size={11} /> verified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-amber-300/80">
                  <ShieldQuestion size={11} /> unverified
                </span>
              )}
            </div>
          </div>
        </div>
        <span className="text-[11px] font-mono text-white/70 shrink-0">
          {score.toFixed(3)}
        </span>
      </div>

      <div className="mt-3 progress h-1.5">
        <span style={{ width: `${score * 100}%` }} />
      </div>

      <button
        onClick={() => setOpen((v) => !v)}
        className="mt-3 text-[12px] text-white/60 hover:text-white inline-flex items-center gap-1"
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {open ? "Hide context" : "Show context"}
      </button>

      {open && (
        <div className="mt-3 text-sm leading-relaxed text-white/80 bg-black/30 border border-white/5 rounded-xl p-3 animate-fadeIn">
          {source.text || <span className="text-white/40">No text available.</span>}
        </div>
      )}
    </article>
  );
}

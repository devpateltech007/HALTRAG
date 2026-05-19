"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Search,
  ScanLine,
  Database,
  FileClock,
  Layers,
  ShieldCheck,
  Sparkles,
  BarChart3,
  Network
} from "lucide-react";
import { getLogs, healthCheck, AuditLogEntry } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<{
    queries: number;
    avgConfidence: number;
    highRisk: number;
  }>({ queries: 0, avgConfidence: 0, highRisk: 0 });
  const [ok, setOk] = useState<boolean | null>(null);
  const [recent, setRecent] = useState<AuditLogEntry[]>([]);

  useEffect(() => {
    healthCheck()
      .then(() => setOk(true))
      .catch(() => setOk(false));
    getLogs(50)
      .then((logs) => {
        const valid = logs.filter((l) => typeof l.confidence === "number");
        const avg =
          valid.length === 0
            ? 0
            : valid.reduce((s, l) => s + (l.confidence ?? 0), 0) / valid.length;
        const high = logs.filter(
          (l) => l.risk === "high" || l.hallucination_risk === "high"
        ).length;
        setStats({ queries: logs.length, avgConfidence: avg, highRisk: high });
        setRecent(logs.slice(0, 5));
      })
      .catch(() => setRecent([]));
  }, []);

  return (
    <div className="space-y-10">
      {/* HERO */}
      <section className="relative overflow-hidden rounded-3xl glass-strong p-8 lg:p-12">
        <div className="absolute inset-0 grid-bg opacity-40 pointer-events-none" />
        <div className="absolute -top-32 -right-20 w-[420px] h-[420px] rounded-full bg-brand-500/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-10 w-[420px] h-[420px] rounded-full bg-violet-500/20 blur-3xl pointer-events-none" />

        <div className="relative max-w-3xl">
          <span className="pill mb-4">
            <Sparkles size={12} className="text-accent-cyan" />
            <span className="text-white/85">Trust-aware AI</span>
          </span>
          <h1 className="text-4xl lg:text-5xl font-semibold tracking-tight leading-[1.05]">
            <span className="gradient-text">HALT-RAG</span>
          </h1>
          <p className="mt-3 text-lg lg:text-xl text-white/85 tracking-tight">
            Trust-Aware Retrieval-Augmented Generation
          </p>
          <p className="mt-3 text-[15px] text-white/65 leading-relaxed max-w-2xl">
            Detect, classify, and localize hallucinations in high-stakes AI answers.
            HALT-RAG separates generation from verification and treats the
            hallucination detector as a probabilistic trust signal — never an oracle.
          </p>

          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/ask" className="btn-primary">
              <Search size={16} />
              Try the Ask Console
              <ArrowRight size={14} />
            </Link>
            <Link href="/about" className="btn-ghost">
              <ShieldCheck size={14} /> How verification works
            </Link>
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            <span className="pill">
              <span
                className={`pill-dot ${ok === false ? "err" : ok === null ? "warn" : ""}`}
              />
              Backend{" "}
              {ok === null ? "connecting…" : ok ? "connected" : "offline"}
            </span>
            <span className="pill">
              <span className="pill-dot" /> Detector active
            </span>
            <span className="pill">
              <span className="pill-dot" /> Dynamic updates enabled
            </span>
            <span className="pill">
              <span className="pill-dot" /> Provider active
            </span>
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<FileClock size={16} className="text-accent-cyan" />}
          label="Recent queries"
          value={String(stats.queries)}
          hint="Audit-logged questions"
        />
        <StatCard
          icon={<BarChart3 size={16} className="text-emerald-300" />}
          label="Avg confidence"
          value={`${(stats.avgConfidence * 100).toFixed(1)}%`}
          hint="Composite trust score"
        />
        <StatCard
          icon={<ScanLine size={16} className="text-amber-300" />}
          label="High-risk answers"
          value={String(stats.highRisk)}
          hint="Routed to human review"
        />
        <StatCard
          icon={<Layers size={16} className="text-violet-300" />}
          label="Detection signals"
          value="4"
          hint="NLI · Sim · Overlap · Retrieval"
        />
      </section>

      {/* PIPELINE */}
      <section className="grid lg:grid-cols-5 gap-4">
        <PipelineStep
          n={1}
          title="Dense retrieval"
          desc="MiniLM embeddings + FAISS index over the curated corpus."
          icon={<Database size={16} className="text-accent-cyan" />}
        />
        <PipelineStep
          n={2}
          title="Generation"
          desc="Gemini answer with extractive fallback for reliability."
          icon={<Sparkles size={16} className="text-violet-300" />}
        />
        <PipelineStep
          n={3}
          title="Sentence grounding"
          desc="NLI + semantic similarity + lexical overlap per sentence."
          icon={<Network size={16} className="text-emerald-300" />}
        />
        <PipelineStep
          n={4}
          title="Detector validation"
          desc="Multi-signal agreement check on the hallucination classifier."
          icon={<ScanLine size={16} className="text-amber-300" />}
        />
        <PipelineStep
          n={5}
          title="Audit trail"
          desc="JSONL audit log of trace, signals, sources, latency."
          icon={<FileClock size={16} className="text-brand-300" />}
        />
      </section>

      {/* RECENT + EXPLAINER */}
      <section className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold tracking-tight">Recent activity</h3>
              <p className="text-[12px] text-white/50">
                Last queries served by the live backend.
              </p>
            </div>
            <Link href="/logs" className="btn-ghost">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          {recent.length === 0 ? (
            <p className="text-sm text-white/45">No queries yet. Run one from the Ask page.</p>
          ) : (
            <ul className="divide-y divide-white/5">
              {recent.map((log, i) => (
                <li key={String(log.query_id ?? i)} className="py-3 flex items-start gap-3">
                  <span className="text-[11px] font-mono text-white/40 w-6 shrink-0 mt-1">
                    #{i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-white/90 truncate">
                      {String(log.question ?? "—")}
                    </p>
                    <div className="mt-1 flex items-center gap-2 text-[11px] text-white/50 flex-wrap">
                      <span className="font-mono">
                        confidence{" "}
                        {typeof log.confidence === "number"
                          ? (log.confidence * 100).toFixed(0)
                          : "—"}
                        %
                      </span>
                      <span>·</span>
                      <span>{String(log.hallucination_type ?? "—")}</span>
                      <span>·</span>
                      <span>
                        risk {String(log.risk ?? log.hallucination_risk ?? "—")}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="glass rounded-2xl p-6">
          <h3 className="text-base font-semibold tracking-tight flex items-center gap-2">
            <ShieldCheck size={16} className="text-accent-cyan" /> Why we trust it
          </h3>
          <p className="mt-3 text-[13px] text-white/70 leading-relaxed">
            The generator (Gemini) and the verifier are <span className="text-white">independent</span>.
            Verification combines four signals — NLI entailment, semantic similarity, lexical
            overlap, retrieval strength — and lowers confidence when those signals disagree.
          </p>
          <p className="mt-3 text-[13px] text-white/70 leading-relaxed">
            Knowledge updates modify the <span className="text-white">vector index</span>, not the
            model weights — so admins can add verified facts in seconds without retraining.
          </p>
          <Link href="/about" className="mt-4 inline-flex btn-ghost">
            Read the methodology <ArrowRight size={12} />
          </Link>
        </div>
      </section>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  hint
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center gap-2 text-[12px] uppercase tracking-wider text-white/55">
        {icon} {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-white tracking-tight">{value}</div>
      <div className="mt-0.5 text-[11px] text-white/45">{hint}</div>
    </div>
  );
}

function PipelineStep({
  n,
  title,
  desc,
  icon
}: {
  n: number;
  title: string;
  desc: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-mono text-white/40">{String(n).padStart(2, "0")}</span>
        <span className="w-7 h-7 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
          {icon}
        </span>
      </div>
      <h4 className="mt-3 text-sm font-semibold tracking-tight text-white">{title}</h4>
      <p className="mt-1 text-[12px] text-white/55 leading-relaxed">{desc}</p>
    </div>
  );
}

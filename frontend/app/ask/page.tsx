"use client";

import { FormEvent, useState } from "react";
import {
  Database,
  FileText,
  Lightbulb,
  Search,
  ShieldAlert,
  Sparkles
} from "lucide-react";
import { queryHALT, QueryResponse } from "@/lib/api";
import { AnswerCard } from "@/components/AnswerCard";
import { SourceCard } from "@/components/SourceCard";
import { SentenceItem, SentenceLegend } from "@/components/SentencePanel";
import { DetectorPanel } from "@/components/DetectorPanel";
import { SectionHeader } from "@/components/SectionHeader";
import { AnswerSkeleton } from "@/components/Skeleton";

const EXAMPLES = [
  "What does HIPAA protect?",
  "What is consideration in contract law?",
  "When is informed consent required?",
  "What is fair use under copyright law?"
];

export default function AskPage() {
  const [question, setQuestion] = useState("What does HIPAA protect?");
  const [topK, setTopK] = useState(5);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    if (!question.trim() || loading) return;
    setLoading(true);
    setError(null);
    setLatencyMs(null);
    const start = performance.now();
    try {
      const data = await queryHALT(question.trim(), topK);
      setResponse(data);
      setLatencyMs(Math.round(performance.now() - start));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* QUERY BAR */}
      <section className="glass-strong rounded-2xl p-6">
        <SectionHeader
          icon={<Search size={16} className="text-accent-cyan" />}
          title="Ask HALT-RAG"
          subtitle="Retrieve evidence, generate, verify, localize, audit."
        />
        <form onSubmit={onAsk} className="space-y-4">
          <div className="relative">
            <textarea
              className="textarea pr-24"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a high-stakes question…"
              rows={3}
            />
            <div className="absolute top-3 right-3 text-[11px] text-white/40 flex items-center gap-1">
              <Sparkles size={11} /> trust-aware
            </div>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <div className="w-32">
              <span className="label-text">Top K</span>
              <select
                className="input"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
              >
                {[3, 5, 8, 10].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" disabled={loading || !question.trim()} className="btn-primary">
              <Search size={14} /> {loading ? "Running…" : "Run Query"}
            </button>
            {latencyMs !== null && (
              <span className="pill">
                <span className="pill-dot" /> {latencyMs} ms
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] text-white/40 mr-1 flex items-center gap-1">
              <Lightbulb size={11} /> Try:
            </span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setQuestion(ex)}
                className="btn-ghost !py-1 !px-2 text-[11px]"
              >
                {ex}
              </button>
            ))}
          </div>
        </form>

        {error && (
          <div className="mt-4 p-3 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-200 text-sm flex items-start gap-2">
            <ShieldAlert size={14} className="mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </section>

      {/* LOADING */}
      {loading && (
        <section className="glass rounded-2xl p-6">
          <AnswerSkeleton />
        </section>
      )}

      {/* RESPONSE */}
      {!loading && response && (
        <>
          <AnswerCard response={response} />

          <DetectorPanel signals={response.detector_signals} />

          <section className="grid lg:grid-cols-2 gap-6">
            <div className="glass rounded-2xl p-6">
              <SectionHeader
                icon={<FileText size={16} className="text-emerald-300" />}
                title="Sentence grounding"
                subtitle="Per-sentence verification with NLI, similarity, overlap."
                right={<SentenceLegend />}
              />
              {response.sentence_analysis.length === 0 ? (
                <p className="text-sm text-white/45">No sentences to analyze.</p>
              ) : (
                <div className="space-y-3">
                  {response.sentence_analysis.map((s, i) => (
                    <SentenceItem key={i} item={s} index={i} />
                  ))}
                </div>
              )}
            </div>

            <div className="glass rounded-2xl p-6">
              <SectionHeader
                icon={<Database size={16} className="text-brand-300" />}
                title="Source evidence"
                subtitle="Top retrieved contexts with score and verification."
                right={
                  <span className="pill">
                    <span className="pill-dot" /> {response.retrieved_sources.length} sources
                  </span>
                }
              />
              {response.retrieved_sources.length === 0 ? (
                <p className="text-sm text-white/45">No sources retrieved.</p>
              ) : (
                <div className="space-y-3">
                  {response.retrieved_sources.map((s, i) => (
                    <SourceCard key={s.source_id + i} source={s} index={i} />
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      )}

      {/* EMPTY STATE */}
      {!loading && !response && !error && (
        <section className="glass rounded-2xl p-10 text-center">
          <div className="inline-flex w-14 h-14 mb-3 rounded-2xl bg-gradient-to-br from-brand-500/20 to-violet-500/20 border border-white/10 items-center justify-center">
            <Search size={20} className="text-accent-cyan" />
          </div>
          <h3 className="text-lg font-semibold tracking-tight">Run a query to begin</h3>
          <p className="text-sm text-white/55 mt-1">
            The result will include grounded answer, sentence-level verification, retrieved
            evidence, and detector reliability signals.
          </p>
        </section>
      )}
    </div>
  );
}

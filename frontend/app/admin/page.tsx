"use client";

import { FormEvent, useState } from "react";
import { CheckCircle2, Database, FilePlus2, MessageSquarePlus, ShieldAlert } from "lucide-react";
import { addDocument, addQA } from "@/lib/api";
import { SectionHeader } from "@/components/SectionHeader";

type Mode = "document" | "qa";

export default function AdminPage() {
  const [mode, setMode] = useState<Mode>("document");
  const [uploader, setUploader] = useState("frontend");
  const [domain, setDomain] = useState("medical");
  const [verified, setVerified] = useState(true);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setSuccess(null);
    setError(null);
    try {
      if (mode === "document") {
        const res = await addDocument({
          text,
          uploader,
          domain,
          verified,
          title: title || undefined
        });
        setSuccess(
          `Knowledge base updated without retraining the LLM. Source ${res.source_id} · ${res.chunks_added} chunk(s).`
        );
        setText("");
        setTitle("");
      } else {
        const res = await addQA({
          question: qaQuestion,
          answer: qaAnswer,
          uploader,
          domain,
          verified
        });
        setSuccess(
          `Knowledge base updated without retraining the LLM. Q&A ${res.source_id} added.`
        );
        setQaQuestion("");
        setQaAnswer("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="glass-strong rounded-2xl p-6">
        <SectionHeader
          icon={<Database size={16} className="text-violet-300" />}
          title="Admin · Knowledge update"
          subtitle="Add verified documents or Q&A pairs without retraining the generator."
        />

        <div className="inline-flex p-1 rounded-xl border border-white/10 bg-white/5 mb-5">
          <button
            type="button"
            onClick={() => setMode("document")}
            className={`px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 transition-all ${
              mode === "document"
                ? "bg-white/10 text-white shadow-inner"
                : "text-white/60 hover:text-white"
            }`}
          >
            <FilePlus2 size={14} /> Document
          </button>
          <button
            type="button"
            onClick={() => setMode("qa")}
            className={`px-4 py-2 rounded-lg text-sm font-medium inline-flex items-center gap-2 transition-all ${
              mode === "qa"
                ? "bg-white/10 text-white shadow-inner"
                : "text-white/60 hover:text-white"
            }`}
          >
            <MessageSquarePlus size={14} /> Q&A pair
          </button>
        </div>

        <form onSubmit={onSubmit} className="grid md:grid-cols-2 gap-5">
          <div>
            <span className="label-text">Uploader</span>
            <input
              className="input"
              value={uploader}
              onChange={(e) => setUploader(e.target.value)}
              placeholder="frontend"
            />
          </div>
          <div>
            <span className="label-text">Domain</span>
            <select
              className="input"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
            >
              {["medical", "legal", "finance", "policy", "general", "enterprise"].map(
                (d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                )
              )}
            </select>
          </div>

          {mode === "document" ? (
            <>
              <div className="md:col-span-2">
                <span className="label-text">Title (optional)</span>
                <input
                  className="input"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. HIPAA — Privacy Rule overview"
                />
              </div>
              <div className="md:col-span-2">
                <span className="label-text">Verified document text</span>
                <textarea
                  className="textarea min-h-[160px]"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste verified content. Will be chunked, embedded, and persisted to the vector store."
                />
              </div>
            </>
          ) : (
            <>
              <div className="md:col-span-2">
                <span className="label-text">Verified question</span>
                <input
                  className="input"
                  value={qaQuestion}
                  onChange={(e) => setQaQuestion(e.target.value)}
                  placeholder="What is the patient's right under HIPAA?"
                />
              </div>
              <div className="md:col-span-2">
                <span className="label-text">Verified answer</span>
                <textarea
                  className="textarea min-h-[140px]"
                  value={qaAnswer}
                  onChange={(e) => setQaAnswer(e.target.value)}
                  placeholder="Provide a concise, evidence-backed answer."
                />
              </div>
            </>
          )}

          <label className="md:col-span-2 inline-flex items-center gap-2 text-sm text-white/85 select-none">
            <input
              type="checkbox"
              checked={verified}
              onChange={(e) => setVerified(e.target.checked)}
              className="w-4 h-4 accent-brand-500"
            />
            Mark as verified source
          </label>

          <div className="md:col-span-2 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={
                busy ||
                (mode === "document" ? !text.trim() : !qaQuestion.trim() || !qaAnswer.trim())
              }
              className="btn-primary"
            >
              {busy ? "Updating…" : "Add to knowledge base"}
            </button>
            <span className="text-[12px] text-white/40">
              The retrieval index reloads automatically. No model retraining needed.
            </span>
          </div>
        </form>

        {success && (
          <div className="mt-5 p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-200 text-sm flex items-start gap-2 animate-fadeIn">
            <CheckCircle2 size={14} className="mt-0.5" />
            <span>{success}</span>
          </div>
        )}
        {error && (
          <div className="mt-5 p-3 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-200 text-sm flex items-start gap-2">
            <ShieldAlert size={14} className="mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </section>

      <section className="glass rounded-2xl p-6 text-[13px] text-white/70 leading-relaxed">
        <h3 className="text-base font-semibold tracking-tight text-white mb-2">
          What happens behind the scenes
        </h3>
        <ol className="list-decimal pl-5 space-y-1">
          <li>Text is chunked and persisted to <code className="text-white/85">data/dynamic_knowledge.jsonl</code>.</li>
          <li>Chunks are embedded with the local MiniLM (or deterministic fallback).</li>
          <li>The FAISS / vector store is rebuilt and the retriever reloads.</li>
          <li>Future queries can now cite this new evidence.</li>
        </ol>
      </section>
    </div>
  );
}

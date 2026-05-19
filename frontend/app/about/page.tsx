import {
  BookOpen,
  Boxes,
  GraduationCap,
  Layers,
  Network,
  ScanLine,
  ShieldCheck,
  Sparkles
} from "lucide-react";

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <section className="glass-strong rounded-2xl p-8 lg:p-10 relative overflow-hidden">
        <div className="absolute -top-24 -right-10 w-[360px] h-[360px] rounded-full bg-violet-500/20 blur-3xl pointer-events-none" />
        <span className="pill mb-4">
          <BookOpen size={12} className="text-accent-cyan" />
          <span className="text-white/85">Methodology</span>
        </span>
        <h1 className="text-3xl lg:text-4xl font-semibold tracking-tight leading-tight">
          <span className="gradient-text">How HALT-RAG verifies its own answers</span>
        </h1>
        <p className="mt-3 text-[15px] text-white/70 leading-relaxed max-w-3xl">
          HALT-RAG is not a chatbot. It is a trust-aware Retrieval-Augmented
          Generation system: the answer-generator and the answer-verifier are
          two independent components, and verification combines multiple
          probabilistic signals rather than a single oracle.
        </p>
      </section>

      <section className="grid lg:grid-cols-2 gap-5">
        <Card
          icon={<Boxes size={16} className="text-accent-cyan" />}
          title="Generator ≠ Verifier"
          body={
            <>
              The <strong className="text-white">generator</strong> is Gemini (with an
              extractive fallback). The <strong className="text-white">verifier</strong>
              uses independent embedding and NLI models. They never share weights or
              representations — so a hallucination in the generator does not propagate
              into the trust signal.
            </>
          }
        />
        <Card
          icon={<Network size={16} className="text-emerald-300" />}
          title="Four independent signals"
          body={
            <>
              For every answer sentence we compute:
              <ul className="list-disc pl-5 mt-2 space-y-1">
                <li>NLI entailment vs. retrieved context</li>
                <li>Semantic similarity between answer and context embeddings</li>
                <li>Lexical overlap of content tokens</li>
                <li>Retrieval strength from dense FAISS search</li>
              </ul>
            </>
          }
        />
        <Card
          icon={<ScanLine size={16} className="text-amber-300" />}
          title="Disagreement lowers confidence"
          body={
            <>
              When the four signals <strong className="text-white">disagree</strong>,
              the detector confidence drops and the answer is flagged uncertain.
              That is the system saying:{" "}
              <em>"send this to a human or a stronger verifier."</em>
            </>
          }
        />
        <Card
          icon={<Layers size={16} className="text-violet-300" />}
          title="Sentence-level localization"
          body={
            <>
              Verification is not just a single number for the whole answer.
              Each sentence is labeled{" "}
              <span className="badge badge-low">grounded</span>{" "}
              <span className="badge badge-medium">uncertain</span>{" "}
              <span className="badge badge-high">hallucinated</span> so the user can see
              <em> which</em> claim to question.
            </>
          }
        />
        <Card
          icon={<Sparkles size={16} className="text-brand-300" />}
          title="Dynamic knowledge updates"
          body={
            <>
              Admin updates modify the{" "}
              <strong className="text-white">vector index</strong>, not the model weights.
              New verified documents and Q&A pairs are chunked, embedded, and reloaded
              into FAISS — the LLM never needs retraining.
            </>
          }
        />
        <Card
          icon={<ShieldCheck size={16} className="text-emerald-300" />}
          title="Probabilistic, not Oracle"
          body={
            <>
              We deliberately avoid claiming hallucination elimination. HALT-RAG offers a
              <strong className="text-white"> probabilistic, interpretable, auditable</strong>
              trust layer for high-stakes domains where transparency matters more than
              over-confidence.
            </>
          }
        />
      </section>

      <section className="glass rounded-2xl p-6 lg:p-8">
        <div className="flex items-center gap-2 mb-3">
          <GraduationCap size={18} className="text-accent-cyan" />
          <h3 className="text-base font-semibold tracking-tight text-white">
            Professor question: “How do we know the hallucination checker is not hallucinating?”
          </h3>
        </div>
        <ol className="list-decimal pl-5 space-y-2 text-[14px] text-white/80 leading-relaxed">
          <li>
            We do not treat the checker as ground truth. It is an{" "}
            <strong className="text-white">aggregate confidence signal</strong>, not a verdict.
          </li>
          <li>
            We combine four <strong className="text-white">independent</strong> signals so a
            single bad signal cannot dominate.
          </li>
          <li>
            When signals disagree, we report{" "}
            <span className="badge badge-medium">low agreement</span> and lower the confidence —
            the system surfaces its own uncertainty rather than hiding it.
          </li>
          <li>
            We separate the generator from the verifier — the verifier’s NLI and embedding models
            were never trained jointly with Gemini.
          </li>
          <li>
            We measure the detector empirically with a curated evaluation set
            (<code className="text-white/80">data/eval/halt_rag_eval.csv</code>) and report results
            in <code className="text-white/80">results/evaluation_report.json</code>, including an
            ablation study over each signal.
          </li>
        </ol>
      </section>
    </div>
  );
}

function Card({ icon, title, body }: { icon: React.ReactNode; title: string; body: React.ReactNode }) {
  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
          {icon}
        </span>
        <h3 className="text-sm font-semibold tracking-tight text-white">{title}</h3>
      </div>
      <div className="text-[13px] text-white/75 leading-relaxed">{body}</div>
    </div>
  );
}

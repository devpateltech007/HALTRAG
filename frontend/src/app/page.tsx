"use client";

import { ChangeEvent, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Database,
  FilePlus2,
  Play,
  ShieldCheck,
  Upload,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

type RetrievedDoc = {
  id: string;
  score: number;
  title: string;
  text_preview: string;
  domain?: string;
};

type Analysis = {
  label: string;
  reliability: string;
  hallucinated: boolean;
  explanation: string;
  entailment_probs_mean?: number | null;
  contradiction_probs_mean?: number | null;
  context_overlap?: number | null;
  grounded_ratio?: number | null;
  unsupported_numbers?: string[] | null;
  unsupported_entities?: string[] | null;
  per_sentence_notes?: string[];
};

type Guardrail = {
  status: string;
  reason: string;
  original_hallucinated: boolean;
  final_hallucinated: boolean;
  fallback_used: boolean;
};

type PipelineResponse = {
  query: string;
  retrieved: RetrievedDoc[];
  context_block: string;
  answer: string;
  generation_mode: string;
  analysis: Analysis;
  raw_answer?: string;
  raw_analysis?: Analysis;
  guardrail?: Guardrail;
  source: "python" | "demo";
};

type UploadResponse = {
  chunks_added: number;
  corpus_count: number;
  chunk_ids: string[];
};

const QUICK_QUERIES = [
  "What is metformin used for?",
  "Does aspirin reduce cardiovascular risk?",
  "Can ibuprofen cause kidney damage?",
  "What is mixture of experts in LLMs?",
];

function formatMetric(value?: number | null) {
  return typeof value === "number" ? value.toFixed(3) : "n/a";
}

export default function Home() {
  const [query, setQuery] = useState(QUICK_QUERIES[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [knowledgeText, setKnowledgeText] = useState("");
  const [knowledgeTitle, setKnowledgeTitle] = useState("Uploaded Knowledge");
  const [knowledgeDomain, setKnowledgeDomain] = useState("custom");
  const [knowledgeFile, setKnowledgeFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const reliabilityTone = useMemo(() => {
    if (!result) return "secondary";
    if (result.analysis.hallucinated) return "destructive";
    if (result.analysis.label === "abstained") return "secondary";
    return "default";
  }, [result]);

  async function runPipeline() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) throw new Error(`Request failed ${res.status}`);
      const data = (await res.json()) as PipelineResponse;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function uploadKnowledge() {
    if (!knowledgeText.trim() && !knowledgeFile) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const form = new FormData();
      form.append("title", knowledgeTitle);
      form.append("domain", knowledgeDomain);
      if (knowledgeText.trim()) form.append("text", knowledgeText.trim());
      if (knowledgeFile) form.append("file", knowledgeFile);

      const res = await fetch("/api/knowledge", {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `Request failed ${res.status}`);
      setUploadResult(data as UploadResponse);
      setKnowledgeText("");
      setKnowledgeFile(null);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setKnowledgeFile(event.target.files?.[0] ?? null);
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-6 md:px-8">
        <header className="flex flex-col gap-3 border-b pb-4 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap gap-2">
              <Badge variant="outline">VeritasRAG</Badge>
              <Badge variant="secondary">Custom 50 QA</Badge>
              <Badge variant="outline">Fail closed</Badge>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight md:text-4xl">Hallucination Guarded RAG</h1>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
              The generator can be wrong. The final answer is accepted only after grounding checks.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm md:w-80">
            <div className="rounded-lg border p-3">
              <p className="text-muted-foreground">Runtime</p>
              <p className="font-semibold">{result ? (result.source === "python" ? "Python" : "Demo") : "--"}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-muted-foreground">Guard</p>
              <p className="font-semibold">{result?.guardrail?.status ?? "--"}</p>
            </div>
          </div>
        </header>

        <section className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldCheck className="h-4 w-4" />
                Ask guarded knowledge
              </CardTitle>
              <CardDescription>Answers are verified against retrieved chunks before display.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-col gap-2 md:flex-row">
                <Input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Enter a question"
                  className="md:flex-1"
                />
                <Button onClick={runPipeline} disabled={loading} className="gap-2 md:w-32">
                  <Play className="h-4 w-4" />
                  {loading ? "Running" : "Run"}
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {QUICK_QUERIES.map((item) => (
                  <Button key={item} variant="secondary" size="sm" onClick={() => setQuery(item)}>
                    {item}
                  </Button>
                ))}
              </div>
              {error ? (
                <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FilePlus2 className="h-4 w-4" />
                Add knowledge
              </CardTitle>
              <CardDescription>Uploaded text is chunked and appended to the local corpus.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-2 md:grid-cols-2">
                <Input value={knowledgeTitle} onChange={(event) => setKnowledgeTitle(event.target.value)} />
                <Input value={knowledgeDomain} onChange={(event) => setKnowledgeDomain(event.target.value)} />
              </div>
              <Textarea
                value={knowledgeText}
                onChange={(event) => setKnowledgeText(event.target.value)}
                placeholder="Paste new evidence"
                className="min-h-24"
              />
              <div className="flex flex-col gap-2 md:flex-row md:items-center">
                <Input type="file" accept=".txt,.md,.csv,.json" onChange={onFileChange} />
                <Button onClick={uploadKnowledge} disabled={uploading} className="gap-2 md:w-36">
                  <Upload className="h-4 w-4" />
                  {uploading ? "Adding" : "Add"}
                </Button>
              </div>
              {knowledgeFile ? <p className="text-xs text-muted-foreground">{knowledgeFile.name}</p> : null}
              {uploadResult ? (
                <div className="rounded-lg border border-green-600/30 bg-green-600/10 p-3 text-sm">
                  Added {uploadResult.chunks_added} chunks. Corpus now has {uploadResult.corpus_count} documents.
                </div>
              ) : null}
              {uploadError ? (
                <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span>{uploadError}</span>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </section>

        {result ? (
          <Tabs defaultValue="answer" className="w-full">
            <TabsList className="grid w-full grid-cols-3 md:w-[520px]">
              <TabsTrigger value="answer">Answer</TabsTrigger>
              <TabsTrigger value="evidence">Evidence</TabsTrigger>
              <TabsTrigger value="audit">Audit</TabsTrigger>
            </TabsList>

            <TabsContent value="answer" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    {result.analysis.hallucinated ? (
                      <AlertCircle className="h-4 w-4 text-destructive" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    )}
                    Final answer
                  </CardTitle>
                  <CardDescription>
                    Mode {result.generation_mode}. Guard {result.guardrail?.status ?? "unknown"}.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-lg border bg-muted/30 p-3 text-sm">{result.query}</div>
                  <p className="leading-7">{result.answer}</p>
                  <Separator />
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={reliabilityTone as "default" | "secondary" | "destructive" | "outline"}>
                      {result.analysis.label}
                    </Badge>
                    <Badge variant="outline">Reliability {result.analysis.reliability}</Badge>
                    <Badge variant="outline">Overlap {formatMetric(result.analysis.context_overlap)}</Badge>
                    <Badge variant="outline">Grounded {formatMetric(result.analysis.grounded_ratio)}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{result.analysis.explanation}</p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="evidence" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Database className="h-4 w-4" />
                    Retrieved evidence
                  </CardTitle>
                  <CardDescription>Top chunks used by the final answer gate.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.retrieved.map((doc) => (
                    <div key={doc.id} className="rounded-lg border border-dashed p-3">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <p className="font-medium">{doc.title}</p>
                        <Badge variant="secondary">{doc.score.toFixed(4)}</Badge>
                        <Badge variant="outline">{doc.domain ?? "n/a"}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{doc.text_preview}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="audit" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Guardrail audit</CardTitle>
                  <CardDescription>{result.guardrail?.reason ?? "No guardrail metadata returned."}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-4">
                    <div className="rounded-lg border p-3">
                      <p className="text-sm text-muted-foreground">Status</p>
                      <p className="font-semibold">{result.guardrail?.status ?? "unknown"}</p>
                    </div>
                    <div className="rounded-lg border p-3">
                      <p className="text-sm text-muted-foreground">Raw hallucinated</p>
                      <p className="font-semibold">{result.guardrail?.original_hallucinated ? "Yes" : "No"}</p>
                    </div>
                    <div className="rounded-lg border p-3">
                      <p className="text-sm text-muted-foreground">Final hallucinated</p>
                      <p className="font-semibold">{result.guardrail?.final_hallucinated ? "Yes" : "No"}</p>
                    </div>
                    <div className="rounded-lg border p-3">
                      <p className="text-sm text-muted-foreground">Fallback</p>
                      <p className="font-semibold">{result.guardrail?.fallback_used ? "Used" : "Not used"}</p>
                    </div>
                  </div>

                  {result.raw_answer && result.raw_answer !== result.answer ? (
                    <div className="rounded-lg border p-3">
                      <p className="mb-2 text-sm font-medium">Raw generator answer</p>
                      <p className="text-sm text-muted-foreground">{result.raw_answer}</p>
                    </div>
                  ) : null}

                  {result.analysis.unsupported_numbers?.length || result.analysis.unsupported_entities?.length ? (
                    <div className="rounded-lg border border-destructive/30 p-3 text-sm">
                      Unsupported facts. Numbers {result.analysis.unsupported_numbers?.join(", ") || "none"}.
                      Entities {result.analysis.unsupported_entities?.join(", ") || "none"}.
                    </div>
                  ) : null}

                  {result.analysis.per_sentence_notes?.length ? (
                    <ScrollArea className="h-36 rounded-lg border p-3">
                      <ul className="space-y-2 text-sm text-muted-foreground">
                        {result.analysis.per_sentence_notes.map((note) => (
                          <li key={note}>{note}</li>
                        ))}
                      </ul>
                    </ScrollArea>
                  ) : null}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        ) : (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            Run a question to see the guarded answer, evidence, and audit trail.
          </div>
        )}
      </div>
    </main>
  );
}

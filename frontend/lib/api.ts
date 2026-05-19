export const API_BASE = (
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE) ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export type Risk = "low" | "medium" | "high";
export type HallucinationType = "faithful" | "factual" | "contextual" | "reasoning";
export type SentenceLabel = "grounded" | "uncertain" | "hallucinated";

export interface RetrievedSource {
  source_id: string;
  text: string;
  score: number;
  verified: boolean;
  metadata: Record<string, unknown>;
}

export interface SentenceAnalysis {
  sentence: string;
  label: SentenceLabel;
  semantic_similarity: number;
  entailment_score: number;
  contradiction_score: number;
  overlap_score: number;
  grounding_score: number;
  best_context: string;
}

export interface DetectorSignals {
  detector_confidence: number;
  agreement_level: string;
  signal_disagreement: boolean;
  explanation: string;
}

export interface QueryResponse {
  question: string;
  answer: string;
  confidence: number;
  risk: Risk;
  hallucination_type: HallucinationType;
  provider: string;
  retrieved_sources: RetrievedSource[];
  sentence_analysis: SentenceAnalysis[];
  detector_signals: DetectorSignals;
}

export interface AuditLogEntry {
  query_id?: string;
  timestamp?: string;
  question?: string;
  answer?: string;
  confidence?: number;
  risk?: Risk;
  hallucination_risk?: Risk;
  hallucination_type?: HallucinationType;
  provider?: string;
  latency_ms?: number;
  detector_signals?: DetectorSignals;
  retrieved_source_ids?: string[];
  [key: string]: unknown;
}

export interface AddDocumentPayload {
  text: string;
  uploader?: string;
  domain?: string;
  verified?: boolean;
  title?: string;
}

export interface AddQAPayload {
  question: string;
  answer: string;
  uploader?: string;
  domain?: string;
  verified?: boolean;
}

export interface KnowledgeUpdateResponse {
  source_id: string;
  chunks_added: number;
  verified: boolean;
  source_type: "document" | "qa_pair";
  vector_store: Record<string, unknown>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export function queryHALT(question: string, topK = 5): Promise<QueryResponse> {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK })
  });
}

export function addDocument(
  payload: AddDocumentPayload
): Promise<KnowledgeUpdateResponse> {
  return request<KnowledgeUpdateResponse>("/admin/add_document", {
    method: "POST",
    body: JSON.stringify({
      uploader: "frontend",
      domain: "general",
      verified: true,
      ...payload
    })
  });
}

export function addQA(payload: AddQAPayload): Promise<KnowledgeUpdateResponse> {
  return request<KnowledgeUpdateResponse>("/admin/add_qa", {
    method: "POST",
    body: JSON.stringify({
      uploader: "frontend",
      domain: "general",
      verified: true,
      ...payload
    })
  });
}

export function getLogs(limit = 50): Promise<AuditLogEntry[]> {
  return request<AuditLogEntry[]>(`/logs?limit=${limit}`);
}

export async function healthCheck(): Promise<{ status: string; service?: string }> {
  return request<{ status: string; service?: string }>("/health");
}

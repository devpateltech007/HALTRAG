import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import path from "node:path";

type PipelineAnalysis = {
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

type PipelineResponse = {
  query: string;
  retrieved: Array<{
    id: string;
    score: number;
    title: string;
    text_preview: string;
    domain?: string;
  }>;
  context_block: string;
  answer: string;
  generation_mode: string;
  analysis: PipelineAnalysis;
  raw_answer?: string;
  raw_analysis?: PipelineAnalysis;
  guardrail?: {
    status: string;
    reason: string;
    original_hallucinated: boolean;
    final_hallucinated: boolean;
    fallback_used: boolean;
  };
  source: "python" | "demo";
};

const DEMO_PASSAGE =
  "Metformin is a first-line medication for type 2 diabetes and can improve glycemic control while reducing hepatic glucose production.";

function demoResponse(query: string): PipelineResponse {
  return {
    query,
    retrieved: [
      {
        id: "demo-001",
        score: 2.5132,
        title: "PubMedQA Snapshot: Metformin and Glycemic Control",
        text_preview: DEMO_PASSAGE,
        domain: "biomedical",
      },
    ],
    context_block: DEMO_PASSAGE,
    answer:
      "Metformin is primarily used to treat type 2 diabetes mellitus. It helps lower blood glucose by decreasing liver glucose production and improving insulin sensitivity.",
    generation_mode: "demo_fallback",
    analysis: {
      label: "faithful",
      reliability: "high",
      hallucinated: false,
      explanation: "Answer is consistent with retrieved evidence and contains no contradiction signal.",
      entailment_probs_mean: 0.82,
      contradiction_probs_mean: 0.06,
      context_overlap: 0.78,
      grounded_ratio: 1,
      unsupported_numbers: [],
      unsupported_entities: [],
      per_sentence_notes: [
        "Sentence 1 aligns with passage support.",
        "Sentence 2 remains grounded in provided context.",
      ],
    },
    raw_answer:
      "Metformin is primarily used to treat type 2 diabetes mellitus. It helps lower blood glucose by decreasing liver glucose production and improving insulin sensitivity.",
    raw_analysis: {
      label: "grounded",
      reliability: "high",
      hallucinated: false,
      explanation: "Demo answer passed grounding checks.",
      entailment_probs_mean: 0.82,
      contradiction_probs_mean: 0.06,
      context_overlap: 0.78,
      grounded_ratio: 1,
      unsupported_numbers: [],
      unsupported_entities: [],
      per_sentence_notes: [],
    },
    guardrail: {
      status: "accepted",
      reason: "Generated answer passed grounding checks.",
      original_hallucinated: false,
      final_hallucinated: false,
      fallback_used: false,
    },
    source: "demo",
  };
}

async function runPythonPipeline(query: string): Promise<PipelineResponse | null> {
  return new Promise((resolve) => {
    const repoRoot = path.resolve(process.cwd(), "..");
    const args = [
      "-m",
      "src.pipeline",
      "--query",
      query,
      "--json",
      "--no-llm",
      "--skip-nli",
    ];

    const child = spawn("python", args, { cwd: repoRoot });
    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("close", (code) => {
      if (code !== 0 || !stdout.trim()) {
        resolve(null);
        return;
      }
      try {
        const parsed = JSON.parse(stdout) as Omit<PipelineResponse, "source">;
        resolve({ ...parsed, source: "python" });
      } catch {
        console.error("Failed to parse Python output:", stderr || stdout);
        resolve(null);
      }
    });

    child.on("error", () => resolve(null));
  });
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { query?: string };
    const query = (body.query ?? "").trim();
    if (!query) {
      return NextResponse.json({ error: "query is required" }, { status: 400 });
    }

    const pythonResult = await runPythonPipeline(query);
    if (pythonResult) return NextResponse.json(pythonResult);

    return NextResponse.json(demoResponse(query));
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }
}

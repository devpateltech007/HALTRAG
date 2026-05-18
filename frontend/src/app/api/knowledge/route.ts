import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import path from "node:path";

type KnowledgeResponse = {
  chunks_added: number;
  corpus_count: number;
  corpus_path: string;
  chunk_ids: string[];
  chunks: Array<{
    id: string;
    title: string;
    text: string;
    domain: string;
    source: string;
  }>;
};

async function appendKnowledge(input: {
  text: string;
  title: string;
  domain: string;
}): Promise<KnowledgeResponse> {
  return new Promise((resolve, reject) => {
    const repoRoot = path.resolve(process.cwd(), "..");
    const args = [
      path.join(repoRoot, "scripts", "add_knowledge.py"),
      "--stdin",
      "--json",
      "--title",
      input.title,
      "--domain",
      input.domain,
      "--source",
      "frontend_upload",
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
    child.on("error", (err) => reject(err));
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr || stdout || "Knowledge update failed"));
        return;
      }
      try {
        const parsed = JSON.parse(stdout) as KnowledgeResponse | { error?: string };
        if ("error" in parsed && parsed.error) {
          reject(new Error(parsed.error));
          return;
        }
        resolve(parsed as KnowledgeResponse);
      } catch {
        reject(new Error(stderr || "Could not parse knowledge update output"));
      }
    });

    child.stdin.write(input.text);
    child.stdin.end();
  });
}

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const titleValue = String(form.get("title") ?? "").trim();
    const domain = String(form.get("domain") ?? "custom").trim() || "custom";
    const textValue = String(form.get("text") ?? "").trim();
    const fileValue = form.get("file");

    let fileText = "";
    let fileName = "";
    if (fileValue instanceof File && fileValue.size > 0) {
      fileName = fileValue.name;
      fileText = (await fileValue.text()).trim();
    }

    const text = [textValue, fileText].filter(Boolean).join("\n\n").trim();
    if (!text) {
      return NextResponse.json({ error: "knowledge text is required" }, { status: 400 });
    }
    if (text.length > 300000) {
      return NextResponse.json({ error: "knowledge text is too large for this demo" }, { status: 413 });
    }

    const result = await appendKnowledge({
      text,
      title: titleValue || fileName || "Uploaded Knowledge",
      domain,
    });
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Invalid knowledge upload";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

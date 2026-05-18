"""
Download PubMedQA (labeled subset) via Hugging Face `datasets`, normalize rows for BM25 ingest,
and write JSON that matches `data/sample_corpus.json` schema (with extra fields tolerated).

Usage (from repo root):
    python scripts/prepare_pubmedqa.py --out data/pubmedqa_labeled_slice.json --max-examples 1200

Requires:
    pip install datasets tqdm  (already in requirements.txt along with transformers/torch optional)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def contexts_to_text(ctx) -> str:
    if isinstance(ctx, dict):
        parts = []
        lbls = ctx.get("labels", [])
        secs = ctx.get("contexts", [])
        meshes = ctx.get("meshes", []) or []
        if lbls or secs:
            for lab, blk in zip(lbls or [""] * len(secs), secs):
                if blk:
                    parts.append(str(blk).strip())
            if parts:
                return "\n".join(parts)
        if meshes:
            return "\n".join(str(m) for m in meshes if m)
    if isinstance(ctx, str):
        return ctx.strip()
    return str(ctx or "").strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "pubmedqa_labeled_slice.json"),
        help="Output JSON path",
    )
    parser.add_argument("--max-examples", type=int, default=1200, help="Subset size for prototyping")
    args = parser.parse_args(argv)

    try:
        from datasets import load_dataset
    except ImportError:
        print("Install datasets first: pip install datasets", file=sys.stderr)
        return 1

    ds = load_dataset("pubmed_qa", "pqa_labeled", split="train")
    n_out = min(int(args.max_examples), len(ds))

    corpus: list[dict] = []
    for i in range(n_out):
        row = ds[i]
        pid = str(row.get("pubid") or row.get("id") or f"pubmed_{i}")
        q = row.get("question") or ""
        ctx = contexts_to_text(row.get("context"))
        if not ctx:
            ctx = contexts_to_text(row.get("contexts"))
        long_ans = (row.get("long_answer") or "").strip()

        blob = ctx
        text = blob if blob else q
        if long_ans:
            text = f"{text}\nEvidence summary (label): {long_ans}"

        corpus.append(
            {
                "id": pid,
                "domain": "medical_pubmedqa",
                "title": q[:280] + ("…" if len(q) > 280 else ""),
                "text": text,
                "final_decision": row.get("final_decision"),
                "source": "pubmedqa_pqa_labeled_hf",
            }
        )

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(corpus)} documents to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

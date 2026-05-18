"""
Append uploaded knowledge to a JSON corpus after chunking it.

Usage:
    python scripts/add_knowledge.py --stdin --title "Lecture Notes" --json
    python scripts/add_knowledge.py --file notes.txt --corpus data/sample_corpus.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.knowledge_base import add_knowledge_text  # noqa: E402


def read_input(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.text:
        parts.append(args.text)
    if args.file:
        parts.append(Path(args.file).read_text(encoding="utf-8"))
    if args.stdin:
        parts.append(sys.stdin.read())
    return "\n\n".join(part for part in parts if part)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chunk and append knowledge to the RAG corpus.")
    parser.add_argument("--corpus", default=str(ROOT / "data" / "sample_corpus.json"))
    parser.add_argument("--title", default="Uploaded Knowledge")
    parser.add_argument("--domain", default="custom")
    parser.add_argument("--source", default="user_upload")
    parser.add_argument("--max-words", type=int, default=140)
    parser.add_argument("--overlap-words", type=int, default=30)
    parser.add_argument("--text", default="")
    parser.add_argument("--file", default="")
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--json", dest="json_out", action="store_true")
    args = parser.parse_args(argv)

    try:
        text = read_input(args)
        result = add_knowledge_text(
            text,
            args.corpus,
            title=args.title,
            domain=args.domain,
            source=args.source,
            max_words=args.max_words,
            overlap_words=args.overlap_words,
        )
    except Exception as exc:  # noqa: BLE001
        if args.json_out:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            print(f"Knowledge update failed: {exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()
    if args.json_out:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Added {payload['chunks_added']} chunks.")
        print(f"Corpus now has {payload['corpus_count']} documents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

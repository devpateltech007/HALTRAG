from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
AUDIT_LOG_PATH = LOG_DIR / "audit.jsonl"
logger = logging.getLogger(__name__)


class AuditLogger:
    """Append-only query logger."""

    def __init__(self, path: str | Path = AUDIT_LOG_PATH):
        self.path = Path(path)

    def log_query(self, entry: dict[str, Any]) -> dict[str, Any]:
        stored = {
            "query_id": entry.get("query_id") or uuid.uuid4().hex,
            "timestamp": entry.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "question": entry.get("question", ""),
            "answer": entry.get("answer", entry.get("model_answer", "")),
            "retrieved_sources": entry.get("retrieved_sources", entry.get("retrieved_source_ids", [])),
            "confidence": entry.get("confidence", 0.0),
            "risk": entry.get("risk", entry.get("hallucination_risk", "medium")),
            "hallucination_type": entry.get("hallucination_type", "contextual"),
            "sentence_analysis": entry.get("sentence_analysis", []),
            "detector_signals": entry.get("detector_signals", {}),
            "provider": entry.get("provider", "unknown"),
        }
        for key, value in entry.items():
            stored.setdefault(key, value)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(stored, ensure_ascii=False, default=str) + "\n")
        logger.info(
            "Logged query %s. risk=%s hallucination_type=%s confidence=%.4f.",
            stored["query_id"],
            stored["risk"],
            stored["hallucination_type"],
            float(stored["confidence"] or 0.0),
        )
        return stored

    def read_logs(
        self,
        limit: int = 100,
        hallucination_type: str | None = None,
        hallucination_risk: str | None = None,
        risk: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        rows = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Skipped invalid JSON audit row in %s.", self.path)
                    continue
                if hallucination_type and entry.get("hallucination_type") != hallucination_type:
                    continue
                selected_risk = risk or hallucination_risk
                if selected_risk and entry.get("risk", entry.get("hallucination_risk")) != selected_risk:
                    continue
                rows.append(entry)
        selected = list(reversed(rows))[: max(1, int(limit or 100))]
        logger.info("Read %d audit log rows from %s.", len(selected), self.path)
        return selected


def log_query(**kwargs: Any) -> dict[str, Any]:
    return AuditLogger().log_query(kwargs)


def read_logs(limit: int = 100) -> list[dict[str, Any]]:
    return AuditLogger().read_logs(limit=limit)


def compact_log_row(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": entry.get("timestamp"),
        "question": entry.get("question"),
        "hallucination_type": entry.get("hallucination_type"),
        "risk": entry.get("risk", entry.get("hallucination_risk")),
        "confidence": entry.get("confidence"),
        "provider": entry.get("provider"),
    }

import re
import string

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "whose",
    "why",
    "with",
}


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Simple tokenizer that removes common stopwords but keeps negations."""
    return [token for token in clean_text(text).split() if token not in STOPWORDS]


def compute_token_overlap(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Jaccard-style overlap between two token lists."""
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def compute_containment(tokens_a: list[str], tokens_b: list[str]) -> float:
    """What fraction of tokens_a are contained in tokens_b.

    Useful for checking how much of a short answer is grounded
    in a longer evidence passage (asymmetric, unlike Jaccard).
    """
    if not tokens_a:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    return len(set_a & set_b) / len(set_a)


def format_results(query: str, evidence: list[dict], answer: str,
                   detection: dict, metrics: dict) -> str:
    """Pretty-print pipeline results for CLI output."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"Query: {query}")
    lines.append("-" * 60)

    lines.append(f"\nRetrieved Evidence ({len(evidence)} docs):")
    for i, doc in enumerate(evidence, 1):
        snippet = doc["text"][:120] + "..." if len(doc["text"]) > 120 else doc["text"]
        lines.append(f"  [{i}] ({doc.get('domain', 'n/a')}) {snippet}")

    lines.append(f"\nGenerated Answer:\n  {answer}")
    lines.append(f"\nHallucination Analysis:")
    lines.append(f"  Type:       {detection['type']}")
    lines.append(f"  Confidence: {detection['confidence']:.2f}")
    lines.append(f"  Reasoning:  {detection['reason']}")

    lines.append(f"\nEvaluation Metrics:")
    for k, v in metrics.items():
        lines.append(f"  {k}: {v:.4f}")

    lines.append("=" * 60)
    return "\n".join(lines)

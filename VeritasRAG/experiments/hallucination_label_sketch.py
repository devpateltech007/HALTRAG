"""
Hallucination Labeling Sketch
==============================
An exploratory prototype that uses simple heuristic rules to classify
a generated answer into hallucination categories.

Categories:
  - factual:     answer contains entities/claims that contradict the context
  - contextual:  answer includes information not present in the context
  - reasoning:   answer draws an invalid conclusion from the context
  - faithfulness: answer distorts or exaggerates what the context says
  - grounded:    answer appears supported by the context (no hallucination detected)

NOTE: This is a rough sketch, not a real detector. The heuristics are brittle
and only meant to test our category definitions on toy examples.

Usage:
    python experiments/hallucination_label_sketch.py
"""

import re
from collections import Counter


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def extract_entities_naive(text):
    """Very rough entity extraction: capitalized multi-word spans."""
    entities = set()
    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text):
        entity = match.group(0)
        if len(entity) > 3:
            entities.add(entity.lower())
    return entities


NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "cannot", "doesn't",
                  "don't", "won't", "isn't", "aren't", "wasn't", "weren't",
                  "hasn't", "haven't", "hadn't", "wouldn't", "shouldn't",
                  "couldn't", "without"}

EXAGGERATION_WORDS = {"always", "never", "all", "every", "none", "absolutely",
                      "certainly", "definitely", "guaranteed", "impossible",
                      "completely", "totally", "entirely"}


def negation_mismatch(context, answer):
    """Check if the answer flips negation relative to the context."""
    ctx_tokens = set(tokenize(context))
    ans_tokens = set(tokenize(answer))
    ctx_negations = ctx_tokens & NEGATION_WORDS
    ans_negations = ans_tokens & NEGATION_WORDS
    return ctx_negations != ans_negations and len(ctx_negations.symmetric_difference(ans_negations)) > 0


def token_coverage(context, answer):
    """What fraction of answer content tokens appear in the context."""
    stopwords = {"a", "an", "the", "is", "are", "was", "were", "it", "in",
                 "of", "to", "and", "for", "on", "with", "that", "this", "by"}
    ans_tokens = [t for t in tokenize(answer) if t not in stopwords]
    if not ans_tokens:
        return 1.0
    ctx_tokens = set(tokenize(context))
    covered = sum(1 for t in ans_tokens if t in ctx_tokens)
    return covered / len(ans_tokens)


def exaggeration_score(answer):
    """Count exaggeration/absolutist language in the answer."""
    ans_tokens = tokenize(answer)
    if not ans_tokens:
        return 0.0
    hits = sum(1 for t in ans_tokens if t in EXAGGERATION_WORDS)
    return hits / len(ans_tokens)


def classify_hallucination(context, answer, threshold_coverage=0.4,
                           threshold_exaggeration=0.05):
    """
    Apply heuristic rules to guess a hallucination type.

    Returns: (label, explanation)
    """
    coverage = token_coverage(context, answer)
    neg_flip = negation_mismatch(context, answer)
    exagg = exaggeration_score(answer)

    ctx_entities = extract_entities_naive(context)
    ans_entities = extract_entities_naive(answer)
    novel_entities = ans_entities - ctx_entities

    if novel_entities:
        return ("factual",
                f"Answer introduces entities not in context: {novel_entities}")

    if neg_flip:
        return ("reasoning",
                "Answer flips negation relative to context — possible invalid inference.")

    if coverage < threshold_coverage:
        return ("contextual",
                f"Low token coverage ({coverage:.2f}) — answer may not be grounded in context.")

    if exagg > threshold_exaggeration:
        return ("faithfulness",
                f"High exaggeration score ({exagg:.2f}) — answer may distort source meaning.")

    return ("grounded",
            f"No hallucination signals detected (coverage={coverage:.2f}).")


EXAMPLES = [
    {
        "name": "Grounded answer",
        "context": "Metformin is a first-line medication for the treatment of type 2 diabetes. "
                   "It works by decreasing glucose production in the liver.",
        "answer": "Metformin is used as a first-line treatment for type 2 diabetes and "
                  "reduces glucose production in the liver.",
    },
    {
        "name": "Factual hallucination (entity)",
        "context": "Warfarin is an anticoagulant monitored using the INR. "
                   "Ciprofloxacin can increase INR.",
        "answer": "Warfarin is monitored using the INR. Amoxicillin is known to "
                  "significantly increase INR levels.",
    },
    {
        "name": "Contextual hallucination (unsupported info)",
        "context": "The HIPAA Privacy Rule establishes national standards for the "
                   "protection of health information.",
        "answer": "HIPAA was enacted in 1996 and includes provisions for electronic "
                  "health records, cybersecurity mandates, and criminal penalties "
                  "for unauthorized disclosure of patient genetic data.",
    },
    {
        "name": "Reasoning hallucination (negation flip)",
        "context": "Metformin does not typically cause hypoglycemia when used alone.",
        "answer": "Metformin causes hypoglycemia frequently, so blood sugar should be "
                  "closely monitored.",
    },
    {
        "name": "Faithfulness hallucination (exaggeration)",
        "context": "Low-dose aspirin is used for secondary prevention of cardiovascular events. "
                   "Its use in primary prevention is more controversial.",
        "answer": "Aspirin is absolutely guaranteed to prevent all cardiovascular events "
                  "and should definitely always be taken by every adult.",
    },
]


def main():
    print("=" * 70)
    print("Hallucination Label Sketch — Heuristic Prototype")
    print("=" * 70)
    print()

    for ex in EXAMPLES:
        label, explanation = classify_hallucination(ex["context"], ex["answer"])
        print(f"Example: {ex['name']}")
        print(f"  Context:  {ex['context'][:80]}...")
        print(f"  Answer:   {ex['answer'][:80]}...")
        print(f"  -> Label:  {label}")
        print(f"  -> Reason: {explanation}")
        print()


if __name__ == "__main__":
    main()

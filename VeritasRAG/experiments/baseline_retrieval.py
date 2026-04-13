"""
Baseline Retrieval Experiment
=============================
A minimal lexical retrieval baseline using token overlap scoring.
This is an early prototype for the HALT-RAG retriever module.

Usage:
    python experiments/baseline_retrieval.py
"""

import json
import os
import re
from collections import Counter


CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample_corpus.json")

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "and", "but", "or", "if", "while", "that", "which", "what", "this",
    "it", "its", "i", "me", "my", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "they", "them", "their",
}


def tokenize(text):
    """Lowercase, strip punctuation, remove stopwords."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def token_overlap_score(query_tokens, doc_tokens):
    """Score a document by the fraction of query tokens that appear in it."""
    if not query_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    doc_set = set(doc_tokens)
    overlap = sum(1 for token in query_counts if token in doc_set)
    return overlap / len(query_counts)


def load_corpus(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def retrieve(query, corpus, top_k=3):
    """Rank corpus documents by token overlap with the query."""
    query_tokens = tokenize(query)
    scored = []
    for doc in corpus:
        doc_tokens = tokenize(doc["title"] + " " + doc["text"])
        score = token_overlap_score(query_tokens, doc_tokens)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def main():
    corpus = load_corpus(CORPUS_PATH)
    print(f"Loaded {len(corpus)} documents from sample corpus.\n")

    test_queries = [
        "What is metformin used for?",
        "What are the elements of medical malpractice?",
        "How does warfarin interact with other drugs?",
        "What is the FDA drug approval process?",
    ]

    for query in test_queries:
        print(f"Query: {query}")
        print("-" * 60)
        results = retrieve(query, corpus, top_k=3)
        for rank, (score, doc) in enumerate(results, 1):
            print(f"  [{rank}] (score={score:.3f}) {doc['id']} — {doc['title']}")
            print(f"       {doc['text'][:100]}...")
        print()


if __name__ == "__main__":
    main()

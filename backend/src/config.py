
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SAMPLE_CORPUS_PATH = os.path.join(PROJECT_ROOT, "data", "sample_corpus.json")
DYNAMIC_KNOWLEDGE_PATH = os.path.join(PROJECT_ROOT, "data", "dynamic_knowledge.jsonl")
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, "data", "vector_store")
AUDIT_LOG_PATH = os.path.join(PROJECT_ROOT, "data", "audit_logs.jsonl")

RETRIEVAL_TOP_K = 3
DENSE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

GENERATION_MODE = "extractive"  # "extractive" or "llm"
LLM_MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"
LLM_LOAD_IN_4BIT = True

HALLUCINATION_TYPES = ["factual", "contextual", "reasoning", "faithfulness"]
NLI_MODEL_NAME = "cross-encoder/nli-deberta-v3-base"
OVERLAP_THRESHOLD = 0.3
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.5
ENABLE_NLI = os.getenv("HALT_RAG_ENABLE_NLI", "0").lower() in {"1", "true", "yes"}
ENABLE_LLM_JUDGE = os.getenv("HALT_RAG_ENABLE_LLM_JUDGE", "0").lower() in {"1", "true", "yes"}

ROUGE_TYPE = "rougeL"

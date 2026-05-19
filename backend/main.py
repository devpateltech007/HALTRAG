from __future__ import annotations
import logging
import os
from typing import Any, Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from src.audit import AuditLogger
from src.confidence import compute_confidence
from src.deep_hallucination_detector import analyze_answer
from src.detector_validation import validate_detector_signals
from src.generation import generate_with_provider
from src.hallucination_classifier import classify_hallucination
from src.knowledge_update import KnowledgeUpdater
from src.retrieval import build_retriever


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://haltrag-cvaqpwp88-devpateltech007s-projects.vercel.app",
]

Risk = Literal["low", "medium", "high"]
HallucinationType = Literal["faithful", "factual", "contextual", "reasoning"]
SentenceLabel = Literal["grounded", "uncertain", "hallucinated"]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=10)
    models: list[str] | None = None


class RetrievedSource(BaseModel):
    source_id: str
    text: str
    score: float
    verified: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class SentenceAnalysisItem(BaseModel):
    sentence: str
    label: SentenceLabel
    semantic_similarity: float
    entailment_score: float
    contradiction_score: float
    overlap_score: float
    grounding_score: float
    best_context: str


class DetectorSignals(BaseModel):
    detector_confidence: float
    agreement_level: str
    signal_disagreement: bool
    explanation: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    risk: Risk
    hallucination_type: HallucinationType
    provider: str
    retrieved_sources: list[RetrievedSource]
    sentence_analysis: list[SentenceAnalysisItem]
    detector_signals: DetectorSignals
    # Compatibility fields for older local tests and notebooks.
    hallucination_risk: Risk | None = None
    retrieved_contexts: list[dict[str, Any]] | None = None
    audit_trace: dict[str, Any] | None = None


class AddDocumentRequest(BaseModel):
    text: str = Field(..., min_length=1)
    uploader: str = "admin"
    domain: str = "general"
    verified: bool = False
    title: str | None = None
    admin_token: str | None = None


class AddQARequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    uploader: str = "admin"
    domain: str = "general"
    verified: bool = True
    admin_token: str | None = None


class KnowledgeUpdateResponse(BaseModel):
    source_id: str
    chunks_added: int
    verified: bool
    source_type: Literal["document", "qa_pair"]
    vector_store: dict[str, Any]


class HaltRAGService:
    def __init__(self):
        self.audit_logger = AuditLogger()
        self.knowledge_updater = KnowledgeUpdater()
        self._retriever = None

    def get_retriever(self):
        if self._retriever is None:
            logger.info("Building retriever for HALT-RAG service.")
            self._retriever = build_retriever()
        return self._retriever

    def reload(self) -> None:
        logger.info("Reloading retriever index after knowledge update.")
        self._retriever = build_retriever(force_rebuild=True)

    def run_query(self, question: str, top_k: int = 5, log: bool = True, **_: Any) -> dict[str, Any]:
        clean_question = (question or "").strip()
        if not clean_question:
            logger.warning("Rejected empty query request.")
            raise ValueError("Question cannot be empty.")

        logger.info("Running query. chars=%d top_k=%d audit_log=%s.", len(clean_question), top_k, log)
        retrieved_sources = self.get_retriever().retrieve(clean_question, top_k=top_k)
        generation = generate_with_provider(clean_question, retrieved_sources)
        answer = generation["answer"]
        sentence_analysis = analyze_answer(clean_question, answer, retrieved_sources)
        retrieval_scores = [float(source.get("score", 0.0) or 0.0) for source in retrieved_sources]
        detector_signals = validate_detector_signals(sentence_analysis, retrieval_scores)
        classification = classify_hallucination(answer, sentence_analysis, retrieved_sources)
        confidence = compute_confidence(
            retrieval_scores=retrieval_scores,
            sentence_results=sentence_analysis,
            detector_signals=detector_signals,
        )

        response = {
            "question": clean_question,
            "answer": answer,
            "confidence": confidence,
            "risk": classification["risk"],
            "hallucination_type": classification["hallucination_type"],
            "provider": generation["provider"],
            "retrieved_sources": [_source_payload(source) for source in retrieved_sources],
            "sentence_analysis": [_sentence_payload(item) for item in sentence_analysis],
            "detector_signals": detector_signals,
        }

        # Compatibility aliases for earlier notebooks/tests.
        response["hallucination_risk"] = response["risk"]
        response["retrieved_contexts"] = response["retrieved_sources"]
        response["audit_trace"] = {"detector_signals": detector_signals}

        if log:
            self.audit_logger.log_query(response)
        logger.info(
            "Query completed. provider=%s risk=%s hallucination_type=%s confidence=%.4f sources=%d sentences=%d.",
            response["provider"],
            response["risk"],
            response["hallucination_type"],
            response["confidence"],
            len(response["retrieved_sources"]),
            len(response["sentence_analysis"]),
        )
        return response

    def add_document(
        self,
        text: str,
        uploader: str | None = None,
        domain: str | None = None,
        verified: bool = False,
        title: str | None = None,
    ) -> dict[str, Any]:
        result = self.knowledge_updater.add_document(
            text=text,
            uploader=uploader,
            domain=domain,
            verified=verified,
            title=title,
        )
        self.reload()
        logger.info(
            "Document update completed. source_id=%s chunks=%d verified=%s.",
            result["source_id"],
            result["chunks_added"],
            result["verified"],
        )
        return result

    def add_qa(
        self,
        question: str,
        answer: str,
        uploader: str | None = None,
        domain: str | None = None,
        verified: bool = True,
    ) -> dict[str, Any]:
        result = self.knowledge_updater.add_qa(
            question=question,
            answer=answer,
            uploader=uploader,
            domain=domain,
            verified=verified,
        )
        self.reload()
        logger.info(
            "Q&A update completed. source_id=%s chunks=%d verified=%s.",
            result["source_id"],
            result["chunks_added"],
            result["verified"],
        )
        return result

    def read_logs(self, limit: int = 100, **filters: Any) -> list[dict[str, Any]]:
        return self.audit_logger.read_logs(limit=limit, **filters)


def create_app(service: Any | None = None) -> FastAPI:
    rag_service = service or HaltRAGService()
    app = FastAPI(title="HALT-RAG API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "halt-rag"}

    @app.post("/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> dict[str, Any]:
        try:
            raw = rag_service.run_query(
                question=request.question,
                top_k=request.top_k,
                models=request.models,
                log=True,
            )
            return _normalize_response(raw)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/admin/add_document", response_model=KnowledgeUpdateResponse)
    def add_document(request: AddDocumentRequest) -> dict[str, Any]:
        try:
            return rag_service.add_document(
                text=request.text,
                uploader=request.uploader,
                domain=request.domain,
                verified=request.verified,
                title=request.title,
            )
        except TypeError:
            return rag_service.add_document(
                text=request.text,
                uploader=request.uploader,
                verified=request.verified,
                title=request.title,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/admin/add_qa", response_model=KnowledgeUpdateResponse)
    def add_qa(request: AddQARequest) -> dict[str, Any]:
        try:
            return rag_service.add_qa(
                question=request.question,
                answer=request.answer,
                uploader=request.uploader,
                domain=request.domain,
                verified=request.verified,
            )
        except TypeError:
            return rag_service.add_qa(
                question=request.question,
                answer=request.answer,
                uploader=request.uploader,
                verified=request.verified,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/logs")
    def logs(
        limit: int = Query(100, ge=1, le=1000),
        hallucination_type: HallucinationType | None = None,
        risk: Risk | None = None,
    ) -> list[dict[str, Any]]:
        return rag_service.read_logs(
            limit=limit,
            hallucination_type=hallucination_type,
            risk=risk,
        )

    return app


def _cors_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return list(dict.fromkeys(DEFAULT_CORS_ORIGINS + origins))


def _normalize_response(raw: dict[str, Any]) -> dict[str, Any]:
    if "retrieved_sources" not in raw and "retrieved_contexts" in raw:
        raw["retrieved_sources"] = raw["retrieved_contexts"]
    if "risk" not in raw:
        raw["risk"] = raw.get("hallucination_risk", "medium")
    if "provider" not in raw:
        raw["provider"] = "unknown"
    if "detector_signals" not in raw:
        raw["detector_signals"] = raw.get("audit_trace", {}).get(
            "detector_signals",
            {
                "detector_confidence": raw.get("confidence", 0.0),
                "agreement_level": "medium",
                "signal_disagreement": False,
                "explanation": "Legacy response did not include final detector validation signals.",
            },
        )
    raw["retrieved_sources"] = [_source_payload(source) for source in raw.get("retrieved_sources", [])]
    raw["sentence_analysis"] = [_sentence_payload(item) for item in raw.get("sentence_analysis", [])]
    raw["hallucination_risk"] = raw["risk"]
    raw["retrieved_contexts"] = raw["retrieved_sources"]
    raw.setdefault("audit_trace", {"detector_signals": raw["detector_signals"]})
    return raw


def _source_payload(source: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(source.get("metadata") or {})
    source_id = source.get("source_id") or source.get("id") or metadata.get("source_id") or "unknown"
    return {
        "source_id": str(source_id),
        "text": str(source.get("text", "")),
        "score": float(source.get("score", 0.0) or 0.0),
        "verified": bool(source.get("verified", metadata.get("verified", False))),
        "metadata": metadata,
    }


def _sentence_payload(item: dict[str, Any]) -> dict[str, Any]:
    signals = item.get("signals") if isinstance(item.get("signals"), dict) else {}
    return {
        "sentence": str(item.get("sentence", "")),
        "label": item.get("label", "uncertain"),
        "semantic_similarity": float(item.get("semantic_similarity", signals.get("semantic_similarity", 0.0)) or 0.0),
        "entailment_score": float(item.get("entailment_score", signals.get("nli_entailment", 0.0)) or 0.0),
        "contradiction_score": float(item.get("contradiction_score", signals.get("nli_contradiction", 0.0)) or 0.0),
        "overlap_score": float(item.get("overlap_score", signals.get("context_overlap", 0.0)) or 0.0),
        "grounding_score": float(item.get("grounding_score", item.get("score", 0.0)) or 0.0),
        "best_context": str(item.get("best_context", item.get("supporting_context", ""))),
    }


app = create_app()

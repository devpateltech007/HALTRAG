import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from backend.api import create_app

class FakeService:
    def run_query(self, question, top_k=5, models=None, log=True):
        return {
            "question": question,
            "answer": "Metformin is used to treat type 2 diabetes.",
            "retrieved_contexts": [
                {
                    "id": "med_001",
                    "title": "Metformin",
                    "domain": "medical",
                    "text": "Metformin is used to treat type 2 diabetes.",
                    "score": 0.9,
                    "source": "test",
                    "metadata": {},
                }
            ],
            "confidence": 0.82,
            "hallucination_risk": "low",
            "hallucination_type": "faithful",
            "sentence_analysis": [
                {
                    "sentence": "Metformin is used to treat type 2 diabetes.",
                    "label": "grounded",
                    "supporting_context": "Metformin is used to treat type 2 diabetes.",
                    "score": 0.88,
                    "source_id": "med_001",
                    "signals": {"semantic_similarity": 0.9},
                }
            ],
            "audit_trace": {"retrieved_source_ids": ["med_001"]},
        }

    def add_document(self, text, uploader=None, verified=False, title=None):
        return {
            "source_id": "doc_test",
            "chunks_added": 1,
            "verified": verified,
            "source_type": "document",
            "vector_store": {"records": 1},
        }

    def add_qa(self, question, answer, uploader=None, verified=True):
        return {
            "source_id": "qa_test",
            "chunks_added": 1,
            "verified": verified,
            "source_type": "qa_pair",
            "vector_store": {"records": 1},
        }

    def read_logs(self, limit=100, hallucination_type=None, hallucination_risk=None):
        return []


def test_query_response_schema():
    client = TestClient(create_app(FakeService()))

    response = client.post(
        "/query",
        json={"question": "What is metformin used for?", "top_k": 3, "models": ["primary"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "What is metformin used for?"
    assert payload["hallucination_type"] == "faithful"
    assert payload["hallucination_risk"] == "low"
    assert 0.0 <= payload["confidence"] <= 1.0
    assert payload["sentence_analysis"][0]["label"] == "grounded"


def test_admin_add_document_schema():
    client = TestClient(create_app(FakeService()))

    response = client.post(
        "/admin/add_document",
        json={"text": "New verified document text.", "verified": True},
    )

    assert response.status_code == 200
    assert response.json()["chunks_added"] == 1

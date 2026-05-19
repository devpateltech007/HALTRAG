from src.knowledge_update import KnowledgeUpdater, load_dynamic_documents

def test_add_document_persists_chunks_and_vector_store(tmp_path):
    updater = KnowledgeUpdater(
        dynamic_path=tmp_path / "dynamic_knowledge.jsonl",
        vector_store_dir=tmp_path / "vector_store",
    )

    result = updater.add_document(
        text="Aspirin may increase bleeding risk in selected patients. " * 10,
        uploader="professor",
        verified=True,
        title="Aspirin update",
    )

    records = load_dynamic_documents(tmp_path / "dynamic_knowledge.jsonl")

    assert result["chunks_added"] >= 1
    assert result["verified"] is True
    assert records[0]["metadata"]["uploader"] == "professor"
    assert (tmp_path / "vector_store" / "hash_embeddings.npy").exists()
    assert (tmp_path / "vector_store" / "metadata.jsonl").exists()


def test_add_qa_marks_source_type(tmp_path):
    updater = KnowledgeUpdater(
        dynamic_path=tmp_path / "dynamic_knowledge.jsonl",
        vector_store_dir=tmp_path / "vector_store",
    )

    result = updater.add_qa(
        question="What does HIPAA protect?",
        answer="HIPAA protects individually identifiable health information.",
        uploader="admin",
    )

    assert result["source_type"] == "qa_pair"
    assert result["verified"] is True

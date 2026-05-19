from src.confidence import compute_confidence, hallucination_risk

def test_confidence_score_is_normalized():
    confidence = compute_confidence(
        retrieved_contexts=[{"score": 0.9}, {"score": 0.6}],
        sentence_analysis=[{"score": 0.8}, {"score": 0.7}],
        detector_validation={"detector_confidence": 0.75},
        model_agreement_score=0.9,
    )

    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.6


def test_hallucination_risk_buckets():
    assert hallucination_risk(0.9, "faithful") == "low"
    assert hallucination_risk(0.55, "faithful") == "medium"
    assert hallucination_risk(0.2, "contextual") == "high"

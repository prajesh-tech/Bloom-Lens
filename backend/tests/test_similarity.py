import pytest
from app.services.similarity_service import SimilarityService


def test_exact_repeat_detection():
    target = "Explain ACID properties of database transactions."
    corpus = [
        {"id": 1, "question_number": "Q1", "original_text": "Explain ACID properties of database transactions."},
        {"id": 2, "question_number": "Q2", "original_text": "What is binary search tree?"},
    ]

    matches = SimilarityService.find_similar_questions(target, corpus)
    assert len(matches) > 0
    assert matches[0]["classification"] == "exact_repeat"
    assert matches[0]["question_id"] == 1


def test_semantic_repeat_detection():
    target = "Explain the ACID properties in DBMS."
    corpus = [
        {"id": 10, "question_number": "Q5", "original_text": "Describe the ACID properties of database transactions."},
    ]

    matches = SimilarityService.find_similar_questions(target, corpus)
    assert len(matches) > 0
    assert matches[0]["similarity_type"] in ["exact_repeat", "semantic_repeat"]
    assert matches[0]["similarity_score"] >= 0.70

import pytest
from app.services.similarity_service import SimilarityService
from app.services.embedding_service import EmbeddingService


def test_exact_repeat_detection():
    target = "Explain ACID properties of database transactions."
    corpus = [
        {"id": 1, "question_number": "Q1", "original_text": "Explain ACID properties of database transactions."},
        {"id": 2, "question_number": "Q2", "original_text": "What is binary search tree?"},
    ]

    target_vec = EmbeddingService.get_embedding(target)
    corpus_data = [(q, EmbeddingService.get_embedding(q["original_text"])) for q in corpus]

    matches = SimilarityService.find_similar_questions_prebuilt(target, target_vec, corpus_data)
    assert len(matches) > 0
    assert matches[0]["classification"] == "exact_repeat"
    assert matches[0]["question_id"] == 1


def test_semantic_repeat_detection():
    target = "Explain the ACID properties in DBMS."
    corpus = [
        {"id": 10, "question_number": "Q5", "original_text": "Describe the ACID properties of database transactions."},
    ]

    target_vec = EmbeddingService.get_embedding(target)
    corpus_data = [(q, EmbeddingService.get_embedding(q["original_text"])) for q in corpus]

    matches = SimilarityService.find_similar_questions_prebuilt(target, target_vec, corpus_data)
    assert len(matches) > 0
    assert matches[0]["similarity_type"] in ["exact_repeat", "semantic_repeat"]
    assert matches[0]["similarity_score"] >= 0.70

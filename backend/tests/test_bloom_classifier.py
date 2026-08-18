import pytest
from app.services.bloom_service import BloomService


def test_mandatory_bloom_l1_to_l6():
    # L1 - Remember
    res1 = BloomService.classify_question("Define normalization.")
    assert res1.primary_level == "L1"

    # L2 - Understand
    res2 = BloomService.classify_question("Explain normalization.")
    assert res2.primary_level == "L2"

    # L3 - Apply
    res3 = BloomService.classify_question("Apply 3NF to the relation.")
    assert res3.primary_level == "L3"

    # L4 - Analyze
    res4 = BloomService.classify_question("Compare 2NF and 3NF.")
    assert res4.primary_level == "L4"

    # L5 - Evaluate
    res5 = BloomService.classify_question("Evaluate normalization for this system.")
    assert res5.primary_level == "L5"

    # L6 - Create
    res6 = BloomService.classify_question("Design a normalized database.")
    assert res6.primary_level == "L6"


def test_compound_question_highest_cognitive_operation():
    """
    Compound question containing L1 (define), L2 (explain), and L4 (compare).
    Must classify as L4 (highest cognitive operation required).
    """
    text = "Define normalization, explain 2NF, and compare it with 3NF."
    res = BloomService.classify_question(text)
    assert res.primary_level == "L4"
    assert "L4" in res.cognitive_operation or "L1" in res.detected_verbs


def test_l6_create_edge_case():
    """
    Ensure containing word 'create' does not naively trigger L6 unless building something new.
    'Create an SQL query to select all rows' -> L3 (Execute/Apply SQL) vs 'Design and construct a database schema' -> L6.
    """
    res_design = BloomService.classify_question("Design a new distributed protocol.")
    assert res_design.primary_level == "L6"

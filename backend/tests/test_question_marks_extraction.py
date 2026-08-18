import pytest
from app.services.marks_service import MarksService
from app.services.question_extraction_service import QuestionExtractionService


def test_marks_extraction_patterns():
    # 1. Explicit marks
    m1, c1 = MarksService.extract_marks("Explain ACID properties. [5 Marks]")
    assert m1 == 5.0
    assert c1 == "high"

    # 2. Multiplication format
    m2, c2 = MarksService.extract_marks("Answer the following questions 2 x 5 = 10")
    assert m2 == 10.0
    assert c2 == "high"

    # 3. Addition format
    m3, c3 = MarksService.extract_marks("Describe ER diagram and schema. (5+5 marks)")
    assert m3 == 10.0
    assert c3 == "high"

    # 4. Bracketed trailing number
    m4, c4 = MarksService.extract_marks("What is functional dependency? (10)")
    assert m4 == 10.0
    assert c4 == "medium"

    # 5. Missing marks
    m5, c5 = MarksService.extract_marks("Define normalization.")
    assert m5 is None
    assert c5 == "low"


def test_question_segmentation_and_hierarchy():
    paper_text = """
    Q1. Define normalization and functional dependency. [5 Marks]

    Q2(a). Explain 2NF and 3NF with examples. [5 Marks]
    Q2(b). Compare 2NF and 3NF normalization. [5 Marks]

    Q3. Answer any 4 out of 5 questions.
    """
    questions = QuestionExtractionService.extract_questions(paper_text)
    assert len(questions) >= 3

    q1 = next((q for q in questions if "Q1" in q["question_number"]), None)
    assert q1 is not None
    assert q1["marks"] == 5.0

    q2a = next((q for q in questions if "Q2(a)" in q["question_number"]), None)
    assert q2a is not None
    assert q2a["parent_number"] == "Q2"


def test_paper_mark_validation():
    paper_text = """
    Q1. Define normalization. [5 Marks]
    Q2. Explain ACID properties. [5 Marks]
    """
    questions = QuestionExtractionService.extract_questions(paper_text)

    # Test exact match (10 max marks == 10 extracted)
    val1 = QuestionExtractionService.validate_paper_marks(10.0, questions, paper_text)
    assert val1["status"] == "valid"
    assert val1["extracted_marks"] == 10.0

    # Test mismatch (20 max marks != 10 extracted)
    val2 = QuestionExtractionService.validate_paper_marks(20.0, questions, paper_text)
    assert val2["status"] == "mismatch" or val2["status"] == "uncertain"

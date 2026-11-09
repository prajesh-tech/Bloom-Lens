import pytest
import docx
import json
from pathlib import Path

from app.services.question_extraction_service import QuestionExtractionService as Extractor
from app.services.marks_service import MarksService
from app.services.docx_service import DOCXService


@pytest.mark.parametrize('name', ['databases', 'algorithms', 'networks', 'mathematics', 'operating_systems'])
def test_realistic_papers(name):
    root = Path(__file__).parent / 'data' / 'extraction'
    expected = json.loads((root / f'{name}.json').read_text())
    questions = Extractor.extract_questions((root / f'{name}.txt').read_text())
    assert [{key: q[key] for key in expected[0]} for q in questions] == expected


@pytest.mark.parametrize('label', ['1.', 'Q1.', 'Q.1', 'Q1)', '1)', 'Question 1:'])
def test_main_labels(label):
    questions = Extractor.extract_questions(f'{label} Define normalization. [5 Marks]')
    assert [(q['question_number'], q['parent_number'], q['marks']) for q in questions] == [('Q1', None, 5)]


def test_explicit_children_and_numbered_nonverbs():
    questions = Extractor.extract_questions('Q1(a) Define a key. [5]\nQ1(b) Explain keys. [5]\n2. Consider relation R(A,B,C). [10]\nQ2(a) Given dependencies, normalize R. [5]')
    assert [(q['question_number'], q['parent_number']) for q in questions] == [('Q1(a)', 'Q1'), ('Q1(b)', 'Q1'), ('Q2', None), ('Q2(a)', 'Q2')]


def test_or_does_not_leak_and_continuations_do_not_split():
    questions = Extractor.extract_questions('Q1. Consider R.\nExplain its dependencies. [5]\nOR\nQ2. Given S, normalize it. [5]\nQ3. Let T be a table. [5]')
    assert [(q['question_number'], q['choice_group']) for q in questions] == [('Q1', 'Q1_OR_GROUP'), ('Q2', 'Q1_OR_GROUP'), ('Q3', None)]


@pytest.mark.parametrize('text,expected', [
    ('Find the inverse of a 3 x 3 matrix.', None),
    ('Evaluate 2+3 using stack.', None),
    ('Find the length of 2 m long wire.', None),
    ('Explain [2 Marks] and compare. (5M)', 5),
    ('Explain [2 Marks] and compare. [7]', 7),
])
def test_marks_require_markers_and_use_last(text, expected):
    assert MarksService.extract_marks(text)[0] == expected


def test_section_marks_reset_and_leaf_validation():
    text = 'PART A [2Q*5M=10 Marks]\nQ1. Explain keys.\nPART B\nQ2. Define a view.'
    questions = Extractor.extract_questions(text)
    assert [q['marks'] for q in questions] == [5, None]
    questions = Extractor.extract_questions('Q1. Answer both. [10]\n(a) Define keys. [5]\n(b) Define views. [5]')
    result = Extractor.validate_paper_marks(10, questions, '')
    assert result['extracted_marks'] == 10
    assert result['status'] == 'valid'


def test_optional_rule_scoped_to_section():
    text = 'SECTION A\nAnswer any 1 out of 2\nQ1. Define keys. [5]\nQ2. Define views. [5]\nSECTION B\nQ3. Explain joins. [10]'
    result = Extractor.validate_paper_marks(15, Extractor.extract_questions(text), text)
    assert result['status'] == 'valid'
    assert result['extracted_marks'] == 15
    assert result['optional_details']['rules'] == [{'section': 'SECTION A', 'n': 1, 'm': 2}]


def test_unresolved_optional_rule_remains_uncertain_even_if_total_matches():
    text = 'SECTION A\nAnswer any 1 out of 2\nQ1. Define keys. [5]\nQ2. Explain joins. [10]'
    result = Extractor.validate_paper_marks(15, Extractor.extract_questions(text), text)
    assert result['status'] == 'uncertain'


def test_or_selection_is_uncertain_even_if_available_total_matches():
    text = 'Q1. Define keys. [5]\nOR\nQ2. Define views. [5]'
    result = Extractor.validate_paper_marks(10, Extractor.extract_questions(text), text)
    assert result['status'] == 'uncertain'


def test_docx_interleaves_tables_and_reports_unknown_pages(tmp_path):
    path = tmp_path / 'paper.docx'
    document = docx.Document()
    document.add_paragraph('Q1. Define keys. [5]')
    document.add_table(rows=1, cols=1).cell(0, 0).text = 'Q2. Explain joins. [5]'
    document.add_paragraph('Q3. Explain views. [5]')
    document.save(path)
    result = DOCXService.extract_text_from_docx(str(path))
    assert result['full_text'].split('\n\n') == ['Q1. Define keys. [5]', 'Q2. Explain joins. [5]', 'Q3. Explain views. [5]']
    assert result['page_count'] is None


@pytest.mark.asyncio
async def test_analytics_counts_leaf_scoring_units(db_session):
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    from app.models.question import Question
    from app.services.analytics_service import AnalyticsService

    subject = Subject(code='LEAF', name='Database Systems')
    db_session.add(subject)
    await db_session.flush()
    paper = QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=10,
                          original_filename='leaf.txt', stored_file_path='leaf.txt')
    db_session.add(paper)
    await db_session.flush()
    parent = Question(question_paper_id=paper.id, question_number='Q1', original_text='Answer both', normalized_text='answer both', marks=10, effective_bloom_level_id=1)
    db_session.add(parent)
    await db_session.flush()
    for letter in ('a', 'b'):
        db_session.add(Question(question_paper_id=paper.id, question_number=f'Q1({letter})', parent_question_id=parent.id,
                                original_text=f'Define {letter}', normalized_text=f'define {letter}', marks=5, effective_bloom_level_id=1))
    await db_session.commit()
    overview = await AnalyticsService.get_overview(db_session)
    assert overview.total_relevant_marks == 10
    assert overview.questions_analyzed == 2
    bloom = await AnalyticsService.get_bloom_analytics(db_session)
    assert bloom.total_marks == 10
    assert bloom.total_questions == 2


@pytest.mark.asyncio
async def test_optional_analytics_reports_selectable_marks_and_uncertainty(db_session):
    from app.models.subject import Subject
    from app.models.question_paper import QuestionPaper
    from app.models.question import Question
    from app.services.analytics_service import AnalyticsService

    subject = Subject(code='OPTION', name='Algorithms')
    db_session.add(subject)
    await db_session.flush()
    paper = QuestionPaper(subject_id=subject.id, examination_type='Internal', maximum_marks=5,
                          original_filename='optional.txt', stored_file_path='optional.txt',
                          optional_question_flag=True, validation_status='valid',
                          validation_metadata={'extracted_marks': 5})
    db_session.add(paper)
    await db_session.flush()
    for number in (1, 2):
        db_session.add(Question(question_paper_id=paper.id, question_number=f'Q{number}',
                               original_text=f'Define {number}', normalized_text=f'define {number}', marks=5))
    await db_session.commit()
    overview = await AnalyticsService.get_overview(db_session)
    assert overview.total_relevant_marks == 5
    bloom = await AnalyticsService.get_bloom_analytics(db_session)
    assert bloom.uncertain_paper_ids == [paper.id]

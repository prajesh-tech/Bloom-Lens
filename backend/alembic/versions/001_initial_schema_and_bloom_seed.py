"""Initial schema and bloom level seed data

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-15 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='instructor'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Subjects Table
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subjects_code'), 'subjects', ['code'], unique=True)
    op.create_index(op.f('ix_subjects_name'), 'subjects', ['name'], unique=False)

    # 3. Bloom Levels Table
    bloom_levels_table = op.create_table(
        'bloom_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bloom_levels_code'), 'bloom_levels', ['code'], unique=True)

    # 4. Question Papers Table
    op.create_table(
        'question_papers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('examination_type', sa.String(length=100), nullable=False),
        sa.Column('maximum_marks', sa.Float(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_file_path', sa.String(length=512), nullable=False),
        sa.Column('upload_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('year_date', sa.String(length=50), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='UPLOADED'),
        sa.Column('extraction_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('validation_status', sa.String(length=50), nullable=False, server_default='NOT_VALIDATED'),
        sa.Column('optional_question_flag', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('validation_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_papers_subject_id'), 'question_papers', ['subject_id'], unique=False)
    op.create_index(op.f('ix_question_papers_processing_status'), 'question_papers', ['processing_status'], unique=False)

    # 5. Questions Table
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('question_paper_id', sa.Integer(), nullable=False),
        sa.Column('parent_question_id', sa.Integer(), nullable=True),
        sa.Column('question_number', sa.String(length=50), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('normalized_text', sa.Text(), nullable=False),
        sa.Column('marks', sa.Float(), nullable=True),
        sa.Column('marks_confidence', sa.String(length=20), nullable=True),
        sa.Column('ai_bloom_level_id', sa.Integer(), nullable=True),
        sa.Column('human_bloom_level_id', sa.Integer(), nullable=True),
        sa.Column('effective_bloom_level_id', sa.Integer(), nullable=True),
        sa.Column('bloom_confidence', sa.Float(), nullable=True),
        sa.Column('bloom_explanation', sa.Text(), nullable=True),
        sa.Column('ai_question_type', sa.String(length=50), nullable=True),
        sa.Column('human_question_type', sa.String(length=50), nullable=True),
        sa.Column('question_type', sa.String(length=50), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('review_status', sa.String(length=50), nullable=False, server_default='AUTO_CLASSIFIED'),
        sa.Column('ai_analysis_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['question_paper_id'], ['question_papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ai_bloom_level_id'], ['bloom_levels.id'], ),
        sa.ForeignKeyConstraint(['human_bloom_level_id'], ['bloom_levels.id'], ),
        sa.ForeignKeyConstraint(['effective_bloom_level_id'], ['bloom_levels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_question_paper_id'), 'questions', ['question_paper_id'], unique=False)
    op.create_index(op.f('ix_questions_parent_question_id'), 'questions', ['parent_question_id'], unique=False)
    op.create_index(op.f('ix_questions_effective_bloom_level_id'), 'questions', ['effective_bloom_level_id'], unique=False)
    op.create_index(op.f('ix_questions_unit'), 'questions', ['unit'], unique=False)
    op.create_index(op.f('ix_questions_review_status'), 'questions', ['review_status'], unique=False)

    # 6. Topics Table
    op.create_table(
        'topics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_subject_id'), 'topics', ['subject_id'], unique=False)
    op.create_index(op.f('ix_topics_name'), 'topics', ['name'], unique=False)

    # 7. Question Topics Table
    op.create_table(
        'question_topics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_topics_question_id'), 'question_topics', ['question_id'], unique=False)
    op.create_index(op.f('ix_question_topics_topic_id'), 'question_topics', ['topic_id'], unique=False)

    # 8. Question Similarities Table
    op.create_table(
        'question_similarities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_question_id', sa.Integer(), nullable=False),
        sa.Column('target_question_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('similarity_type', sa.String(length=50), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.Column('similarity_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_similarities_source_question_id'), 'question_similarities', ['source_question_id'], unique=False)
    op.create_index(op.f('ix_question_similarities_target_question_id'), 'question_similarities', ['target_question_id'], unique=False)

    # Seed Bloom Level Data (L1 to L6)
    op.bulk_insert(
        bloom_levels_table,
        [
            {
                "id": 1,
                "code": "L1",
                "name": "Remember",
                "description": "Recall facts and basic concepts",
                "keywords": ["define", "list", "identify", "state", "name", "recall", "repeat", "label", "match", "select"]
            },
            {
                "id": 2,
                "code": "L2",
                "name": "Understand",
                "description": "Explain ideas or concepts",
                "keywords": ["explain", "describe", "summarize", "discuss", "interpret", "classify", "outline", "paraphrase"]
            },
            {
                "id": 3,
                "code": "L3",
                "name": "Apply",
                "description": "Use information in new situations",
                "keywords": ["apply", "demonstrate", "calculate", "solve", "execute", "implement", "illustrate", "use", "compute"]
            },
            {
                "id": 4,
                "code": "L4",
                "name": "Analyze",
                "description": "Draw connections among ideas",
                "keywords": ["analyze", "compare", "differentiate", "contrast", "distinguish", "examine", "deconstruct", "investigate"]
            },
            {
                "id": 5,
                "code": "L5",
                "name": "Evaluate",
                "description": "Justify a stand or decision",
                "keywords": ["evaluate", "justify", "critique", "assess", "judge", "defend", "recommend", "rate", "appraise"]
            },
            {
                "id": 6,
                "code": "L6",
                "name": "Create",
                "description": "Produce new or original work",
                "keywords": ["design", "develop", "construct", "formulate", "architect", "propose", "build", "invent", "devise"]
            }
        ]
    )


def downgrade() -> None:
    op.drop_table('question_similarities')
    op.drop_table('question_topics')
    op.drop_table('topics')
    op.drop_table('questions')
    op.drop_table('question_papers')
    op.drop_table('bloom_levels')
    op.drop_table('subjects')
    op.drop_table('users')

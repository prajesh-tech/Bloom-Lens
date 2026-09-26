"""Add Course, CourseOutcome, and QuestionCourseOutcome tables and course_id to QuestionPaper

Revision ID: c0a1b2c3d4e5
Revises: 04d536a736a7
Create Date: 2026-09-26 04:36:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0a1b2c3d4e5'
down_revision: Union[str, None] = '04d536a736a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Courses Table
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_code', sa.String(length=50), nullable=False),
        sa.Column('course_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_courses_course_code'), 'courses', ['course_code'], unique=True)
    op.create_index(op.f('ix_courses_course_name'), 'courses', ['course_name'], unique=False)

    # 2. Course Outcomes Table
    op.create_table(
        'course_outcomes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'code', name='uq_course_outcome_course_code'),
    )
    op.create_index(op.f('ix_course_outcomes_course_id'), 'course_outcomes', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_outcomes_code'), 'course_outcomes', ['code'], unique=False)

    # 3. Question Course Outcomes Table (Join & Mapping Table)
    op.create_table(
        'question_course_outcomes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('course_outcome_id', sa.Integer(), nullable=False),
        sa.Column('semantic_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('concept_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('bloom_consistency_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('final_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ai_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('llm_verified', sa.String(length=50), nullable=False, server_default='skipped'),
        sa.Column('llm_reason', sa.Text(), nullable=True),
        sa.Column('human_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('human_override', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_outcome_id'], ['course_outcomes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id', 'course_outcome_id', name='uq_question_co_mapping'),
    )
    op.create_index(op.f('ix_question_course_outcomes_question_id'), 'question_course_outcomes', ['question_id'], unique=False)
    op.create_index(op.f('ix_question_course_outcomes_course_outcome_id'), 'question_course_outcomes', ['course_outcome_id'], unique=False)

    # 4. Add course_id to question_papers
    op.add_column('question_papers', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_question_papers_course_id'), 'question_papers', ['course_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_question_papers_course_id'), table_name='question_papers')
    op.drop_column('question_papers', 'course_id')

    op.drop_index(op.f('ix_question_course_outcomes_course_outcome_id'), table_name='question_course_outcomes')
    op.drop_index(op.f('ix_question_course_outcomes_question_id'), table_name='question_course_outcomes')
    op.drop_table('question_course_outcomes')

    op.drop_index(op.f('ix_course_outcomes_code'), table_name='course_outcomes')
    op.drop_index(op.f('ix_course_outcomes_course_id'), table_name='course_outcomes')
    op.drop_table('course_outcomes')

    op.drop_index(op.f('ix_courses_course_name'), table_name='courses')
    op.drop_index(op.f('ix_courses_course_code'), table_name='courses')
    op.drop_table('courses')

"""Local reviewers, revocable browser sessions, and question revision history.

Rollback deletes credentials, active sessions, and revision history; export first.
"""
from alembic import op
import sqlalchemy as sa

revision = 'reviewers_20261109'
down_revision = 'upload_jobs_20261109'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('reviewers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(30), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False))
    op.create_table('reviewer_sessions',
        sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('reviewers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('csrf_token', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('question_revisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('questions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('acting_user', sa.String(150), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('old_value', sa.JSON(), nullable=False),
        sa.Column('new_value', sa.JSON(), nullable=False))
    op.create_index('ix_question_revisions_question_id', 'question_revisions', ['question_id'])


def downgrade():
    op.drop_table('question_revisions')
    op.drop_table('reviewer_sessions')
    op.drop_table('reviewers')

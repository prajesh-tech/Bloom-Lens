"""Persist upload hashes and worker failures.

Rollback removes hash uniqueness and failure details; retain a backup first.
Existing papers keep null hashes and are not retroactively deduplicated.
"""
from alembic import op
import sqlalchemy as sa

revision = 'upload_jobs_20261109'
down_revision = 'c0a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('question_papers') as batch:
        batch.add_column(sa.Column('file_hash', sa.String(64), nullable=True))
        batch.add_column(sa.Column('error_message', sa.String(512), nullable=True))
        batch.create_unique_constraint('uq_paper_subject_hash', ['subject_id', 'file_hash'])


def downgrade():
    with op.batch_alter_table('question_papers') as batch:
        batch.drop_constraint('uq_paper_subject_hash', type_='unique')
        batch.drop_column('error_message')
        batch.drop_column('file_hash')

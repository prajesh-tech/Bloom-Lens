"""Persist versioned question embeddings. Rollback discards cached vectors only."""
from alembic import op
import sqlalchemy as sa

revision = 'embeddings_20261109'
down_revision = 'reviewers_20261109'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('questions') as batch:
        batch.add_column(sa.Column('embedding_vector', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('embedding_backend', sa.String(255), nullable=True))
        batch.add_column(sa.Column('embedding_metadata', sa.JSON(), nullable=True))
    with op.batch_alter_table('topics') as batch:
        batch.add_column(sa.Column('is_managed', sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade():
    with op.batch_alter_table('topics') as batch:
        batch.drop_column('is_managed')
    with op.batch_alter_table('questions') as batch:
        batch.drop_column('embedding_metadata')
        batch.drop_column('embedding_backend')
        batch.drop_column('embedding_vector')

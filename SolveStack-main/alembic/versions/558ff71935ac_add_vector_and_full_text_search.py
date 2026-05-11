"""Add vector and full-text search

Revision ID: 558ff71935ac
Revises: b4fb1a66c1fb
Create Date: 2026-03-03 10:24:31.412078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '558ff71935ac'
down_revision: Union[str, Sequence[str], None] = 'b4fb1a66c1fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Add search_vector column (TSVECTOR)
    op.add_column('problems', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    
    # Drop and recreate embedding column as VECTOR(384)
    # Direct cast from JSON to VECTOR is not supported in Postgres
    op.execute("ALTER TABLE problems DROP COLUMN IF EXISTS embedding;")
    op.execute("ALTER TABLE problems ADD COLUMN embedding vector(384);")
    
    # Create GIN index for full-text search
    op.execute("CREATE INDEX IF NOT EXISTS problems_search_idx ON problems USING GIN (search_vector);")
    
    # Create HNSW index for vector search
    op.execute("CREATE INDEX IF NOT EXISTS problems_embedding_idx ON problems USING hnsw (embedding vector_cosine_ops);")
    
    # Populate search_vector
    op.execute("""
        UPDATE problems 
        SET search_vector = to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(description, ''))
        WHERE search_vector IS NULL;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('problems_embedding_idx', table_name='problems')
    op.drop_index('problems_search_idx', table_name='problems')
    op.drop_column('problems', 'search_vector')

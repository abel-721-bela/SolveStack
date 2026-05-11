from database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def optimize_index():
    logger.info("Optimizing index for cosine similarity...")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("DROP INDEX IF EXISTS problems_embedding_idx"))
            conn.execute(text("CREATE INDEX problems_embedding_idx ON problems USING hnsw (embedding vector_cosine_ops)"))
            logger.info("Index created: problems_embedding_idx (HNSW + vector_cosine_ops)")

if __name__ == "__main__":
    optimize_index()

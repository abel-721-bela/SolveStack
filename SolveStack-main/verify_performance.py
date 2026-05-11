from database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_performance():
    logger.info("Running EXPLAIN ANALYZE for semantic search...")
    # Mocking a vector [0.1]*384 for the query
    vector_str = "[" + ",".join(["0.1"]*384) + "]"
    
    query = text(f"""
        EXPLAIN ANALYZE 
        SELECT ps_id, title, (1 - (embedding <=> '{vector_str}')) as score 
        FROM problems 
        ORDER BY embedding <=> '{vector_str}' 
        LIMIT 10
    """)
    
    with engine.connect() as conn:
        res = conn.execute(query)
        for row in res:
            print(row[0])

if __name__ == "__main__":
    verify_performance()

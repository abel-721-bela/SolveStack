from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    def get_candidates(self, db: Session, query_embedding: list, keyword_query: str, limit: int = 30) -> list[int]:
        """
        Stage 1: Retrieve broad candidates from Vector and Keyword search.
        Returns a list of unique problem IDs (ps_id).
        """
        # 1. Vector Search Query
        vector_sql = text("""
            SELECT ps_id
            FROM problems
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> cast(:embedding as vector)
            LIMIT :limit
        """)
        
        # 2. Keyword Search (FTS) Query
        # Use websearch_to_tsquery for more flexible Google-like queries
        keyword_sql = text("""
            SELECT ps_id
            FROM problems
            WHERE search_vector @@ websearch_to_tsquery('english', :query)
            ORDER BY ts_rank(search_vector, websearch_to_tsquery('english', :query)) DESC
            LIMIT :limit
        """)
        
        try:
            # Execute Vector Search
            vector_res = db.execute(vector_sql, {
                "embedding": str(query_embedding),
                "limit": limit
            }).fetchall()
            
            # Execute Keyword Search
            keyword_res = db.execute(keyword_sql, {
                "query": keyword_query,
                "limit": limit
            }).fetchall()
            
            # Combine IDs
            candidate_ids = set()
            for row in vector_res:
                candidate_ids.add(row[0])
            for row in keyword_res:
                candidate_ids.add(row[0])
                
            logger.info(f"Stage 1: Retrieved {len(candidate_ids)} candidates (Vector: {len(vector_res)}, Keyword: {len(keyword_res)})")
            return list(candidate_ids)
            
        except Exception as e:
            logger.error(f"Error in Stage 1 retrieval: {e}")
            import traceback
            traceback.print_exc()
            return []

# Singleton instance
_retrieval_service = None
def get_retrieval_service():
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service

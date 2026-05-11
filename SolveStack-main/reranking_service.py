import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from models import Problem
import logging

logger = logging.getLogger(__name__)

class RerankingService:
    def __init__(self):
        # Default Weights
        self.w_semantic = float(os.getenv("SEARCH_W_SEMANTIC", 0.50))
        self.w_keyword = float(os.getenv("SEARCH_W_KEYWORD", 0.25))
        self.w_tag = float(os.getenv("SEARCH_W_TAG", 0.15))
        self.w_title_boost = float(os.getenv("SEARCH_W_TITLE_BOOST", 0.05))
        self.w_intent_boost = float(os.getenv("SEARCH_W_INTENT_BOOST", 0.05))

    def rerank(self, db: Session, candidate_ids: list[int], semantic_query_embedding: list, keyword_query: str, query_tags: list[str] = None) -> list:
        """
        Stage 2: Re-rank candidates using weighted hybrid scoring and intent boosts.
        """
        if not candidate_ids:
            return []

        # 1. Build the boosted scoring SQL
        # We use CASE statements for intent boosts
        
        # Difficulty intent matching
        diff_intent_sql = "0"
        difficulty_terms = {"easy": 1, "medium": 2, "hard": 3, "beginner": 1, "advanced": 3, "difficult": 3}
        query_words = set(keyword_query.lower().split())
        matched_diff = None
        for word, val in difficulty_terms.items():
            if word in query_words:
                matched_diff = val
                break
        
        if matched_diff is not None:
            diff_intent_sql = f"CASE WHEN difficulty_level = {matched_diff} THEN 1 ELSE 0 END"

        # Semantic score: 1 - cosine distance
        sem_score_sql = "(1 - (embedding <=> :query_embedding))"
        
        # Keyword score: ts_rank
        kw_score_sql = "ts_rank(search_vector, plainto_tsquery('english', :keyword_query))"
        
        # Tag score: intersection count (normalized to 1 if matched)
        tag_score_sql = "0"
        if query_tags:
            tag_score_sql = """
                CASE WHEN 
                (SELECT count(*) 
                 FROM json_array_elements_text(CASE WHEN json_typeof(tags) = 'array' THEN tags ELSE '[]'::json END) AS t 
                 WHERE t.value = ANY(:query_tags)) > 0 THEN 1 ELSE 0 END
            """

        # Title Boost: Exact token match in title
        title_boost_sql = "CASE WHEN title ILIKE :title_pattern THEN 1 ELSE 0 END"
        
        # Intent Boost: Description token appearance + Difficulty Match
        # Check if first 100 chars of description contain query keywords
        desc_boost_sql = f"((CASE WHEN substring(description from 1 for 100) ILIKE :title_pattern THEN 1 ELSE 0 END) + ({diff_intent_sql})) / 2.0"

        final_score_sql = f"""
            (
                (:w_sem * {sem_score_sql}) + 
                (:w_kw * {kw_score_sql}) + 
                (:w_tag * {tag_score_sql}) + 
                (:w_title * {title_boost_sql}) + 
                (:w_intent * {desc_boost_sql})
            )
        """

        sql = text(f"""
            SELECT *, 
                   {final_score_sql} AS final_overall_score,
                   {sem_score_sql} AS s_score,
                   {kw_score_sql} AS k_score,
                   {tag_score_sql} AS t_score
            FROM problems
            WHERE ps_id = ANY(:candidate_ids)
            ORDER BY final_overall_score DESC
        """)

        params = {
            "query_embedding": str(semantic_query_embedding),
            "keyword_query": keyword_query,
            "query_tags": query_tags or [],
            "candidate_ids": candidate_ids,
            "title_pattern": f"%{keyword_query}%" if keyword_query else "%",
            "w_sem": self.w_semantic,
            "w_kw": self.w_keyword,
            "w_tag": self.w_tag,
            "w_title": self.w_title_boost,
            "w_intent": self.w_intent_boost
        }

        try:
            results = db.execute(sql, params).fetchall()
            
            final_problems = []
            for row in results:
                row_dict = dict(row._mapping)
                score = float(row_dict.pop('final_overall_score', 0) or 0.0)
                s_score = float(row_dict.pop('s_score', 0) or 0.0)
                k_score = float(row_dict.pop('k_score', 0) or 0.0)
                t_score = float(row_dict.pop('t_score', 0) or 0.0)
                
                # Construct Problem object
                problem = Problem(**{k: v for k, v in row_dict.items() if k in Problem.__table__.columns})
                
                # Attach scores for the response
                problem.search_scores = {
                    "semantic": round(s_score, 3),
                    "keyword": round(k_score, 3),
                    "tag": round(t_score, 3),
                    "final": round(score, 3)
                }
                final_problems.append(problem)
                
            return final_problems
            
        except Exception as e:
            logger.error(f"Error in Stage 2 re-ranking: {e}")
            import traceback
            traceback.print_exc()
            return []

# Singleton instance
_reranking_service = None
def get_reranking_service():
    global _reranking_service
    if _reranking_service is None:
        _reranking_service = RerankingService()
    return _reranking_service

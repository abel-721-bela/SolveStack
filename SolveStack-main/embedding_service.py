import torch
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            logger.info("Initializing EmbeddingService singleton...")
            # Load model once
            # all-MiniLM-L6-v2 produces 384-dimensional embeddings
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            if torch.cuda.is_available():
                cls._model = cls._model.to('cuda')
                logger.info("Using CUDA for embeddings")
            else:
                logger.info("Using CPU for embeddings")
        return cls._instance

    def generate_embedding(self, title: str, description: str = "", tags: list = None) -> list:
        """
        Generate a normalized 384-dimensional embedding for a problem.
        Format: "Title: {title}. Description: {description}. Tags: {comma_separated_tags}"
        """
        if not title:
            return None

        # Standardize input
        tags_str = ", ".join(tags) if tags else ""
        text = f"Title: {title.strip()}. Description: {description.strip()}. Tags: {tags_str}"
        
        # Validation: Max query length 500 characters
        if len(text) > 500:
            text = text[:500]
            logger.warning(f"Input text truncated to 500 chars for embedding.")

        try:
            # Generate normalized embedding
            embedding = self._model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def generate_batch_embeddings(self, texts: list[str]):
        """Generate normalized embeddings for a batch of texts"""
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    @torch.no_grad()
    def generate_query_embedding(self, query: str) -> list:
        """
        Specialized method for query embedding with caching support.
        """
        from functools import lru_cache
        
        # We need a wrapper because lru_cache is instance-bound or we can use a simple dict
        if not hasattr(self, "_query_cache"):
            self._query_cache = {}
            
        if query in self._query_cache:
            return self._query_cache[query]
            
        # Limit query length
        clean_query = query[:500]
        embedding = self._model.encode(clean_query, normalize_embeddings=True).tolist()
        
        # Simple cache management (keep last 100 queries)
        if len(self._query_cache) > 100:
            self._query_cache.clear() # Primitive but safe for simple LRU intent
            
        self._query_cache[query] = embedding
        return embedding

# Singleton instance access
def get_embedding_service():
    return EmbeddingService()

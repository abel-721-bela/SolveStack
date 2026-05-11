import re
import logging

logger = logging.getLogger(__name__)

class QueryProcessingService:
    def __init__(self):
        # Trivial stopwords
        self.stopwords = {
            "a", "an", "the", "in", "on", "at", "for", "to", "of", "with", "by",
            "is", "are", "was", "were", "be", "been", "being",
            "and", "or", "but", "so", "if", "then", "else", "when", "how", "what", "where", "why"
        }
        
        # Small custom synonym map for technical domain
        self.synonyms = {
            "array": ["list", "sequence", "vector"],
            "list": ["array", "sequence"],
            "add": ["sum", "total", "plus", "combine"],
            "sum": ["add", "total"],
            "fast": ["efficient", "optimized", "quick", "performance"],
            "slow": ["inefficient", "bottleneck"],
            "number": ["integer", "digit", "numeric", "val"],
            "integer": ["number", "int"],
            "string": ["text", "char"],
            "find": ["search", "detect", "lookup", "locate"],
            "search": ["find", "lookup"],
            "remove": ["delete", "drop", "clear"],
            "delete": ["remove", "drop"],
            "map": ["hashmap", "dictionary", "dict", "mapping"],
            "dict": ["map", "hashmap", "dictionary"],
            "easy": ["beginner", "simple", "basic"],
            "hard": ["advanced", "complex", "difficult"],
            "difficult": ["hard", "complex", "advanced"]
        }

    def normalize(self, text: str) -> str:
        """Lowercase, strip punctuation, collapse whitespace"""
        if not text:
            return ""
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def remove_stopwords(self, text: str) -> str:
        """Remove trivial words that don't add much intent"""
        tokens = text.split()
        filtered = [t for t in tokens if t not in self.stopwords]
        return " ".join(filtered)

    def expand_query(self, text: str) -> str:
        """
        Expand query with synonyms for keyword search.
        Boosts original query terms by including them alongside expansions.
        """
        tokens = text.split()
        expanded_tokens = list(tokens) # Start with original tokens
        
        for token in tokens:
            if token in self.synonyms:
                expanded_tokens.extend(self.synonyms[token])
        
        # Return unique tokens while preserving some order (original first)
        seen = set()
        unique_expanded = []
        for t in expanded_tokens:
            if t not in seen:
                unique_expanded.append(t)
                seen.add(t)
                
        return " ".join(unique_expanded)

    def process_query(self, query: str):
        """
        Main entry point for query processing.
        Returns:
            - cleaned_query: For semantic search (minimal noise, original intent preserved)
            - expanded_query: For keyword search (includes synonyms)
        """
        normalized = self.normalize(query)
        
        # For semantic search, we want the natural language but cleaned
        semantic_query = self.remove_stopwords(normalized)
        
        # For keyword search, we expand with synonyms
        keyword_query = self.expand_query(semantic_query)
        
        return {
            "original": query,
            "semantic": semantic_query or normalized,
            "keyword": keyword_query or normalized
        }

# Singleton instance
_query_processor = None
def get_query_processor():
    global _query_processor
    if _query_processor is None:
        _query_processor = QueryProcessingService()
    return _query_processor

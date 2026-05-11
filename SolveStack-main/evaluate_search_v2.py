import time
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from search_service import get_search_service

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Evaluation Queries and Ground Truth (Expected ps_id)
# These are mapped from the actual database state
EVAL_DATA = [
    {"query": "jwt auth spa", "expected": 4},
    {"query": "postgress pool error", "expected": 3}, # Intent: Handling typos/synonyms
    {"query": "react browser apis on mount", "expected": 51},
    {"query": "antigravity version outdated", "expected": 9},
    {"query": "claude cli auth mode mismatch", "expected": 11},
    {"query": "spanish translation request", "expected": 14},
    {"query": "form loop trigger", "expected": 19},
    {"query": "sveltkit runtime control module missing", "expected": 25},
    {"query": "nextjs memory usage dev", "expected": 28},
    {"query": "framer motion shared layout app router", "expected": 29},
    {"query": "interpolated translateY android view jump", "expected": 35},
    {"query": "docker network frontend backend", "expected": 6},
    {"query": "python menu aligned prices", "expected": 40},
    {"query": "excel slow web app session", "expected": 41},
    {"query": "mediapipe solutions attribute error", "expected": 42},
    {"query": "trade execution automated", "expected": 43},
    {"query": "neo4j windows module not found", "expected": 44},
    {"query": "multiprocessing pickling error decorators", "expected": 45},
    {"query": "svg pan zoom scroll swipe", "expected": 47},
    {"query": "javascript image overlay", "expected": 48}
]

def calculate_metrics(results, expected_id, k=5):
    """Calculate P@k and Reciprocal Rank"""
    found_at = -1
    for i, res in enumerate(results[:k]):
        if res.ps_id == expected_id:
            found_at = i + 1
            break
    
    precision_at_k = 1.0 / k if found_at != -1 else 0.0
    reciprocal_rank = 1.0 / found_at if found_at != -1 else 0.0
    
    return precision_at_k, reciprocal_rank

def run_evaluation():
    db = SessionLocal()
    search_service = get_search_service()
    
    total_p5 = 0
    total_mrr = 0
    total_latency = 0
    
    print(f"\n{'Query':<45} | {'Rank':<5} | {'Latency':<10}")
    print("-" * 65)
    
    for item in EVAL_DATA:
        query = item["query"]
        expected = item["expected"]
        
        results, metadata = search_service.intent_aware_search(db, query, limit=5)
        
        # Calculate metrics
        p5, rr = calculate_metrics(results, expected, k=5)
        
        total_p5 += p5
        total_mrr += rr
        total_latency += metadata["latency_ms"]
        
        rank_str = f"{int(1/rr)}" if rr > 0 else "N/A"
        print(f"{query[:44]:<45} | {rank_str:<5} | {metadata['latency_ms']:>6.2f}ms")

    num_queries = len(EVAL_DATA)
    avg_p5 = (total_p5 / num_queries) * 5 # Scale back to average success at 5
    mrr = total_mrr / num_queries
    avg_latency = total_latency / num_queries
    
    print("=" * 65)
    print(f"Final Metrics (N={num_queries}):")
    print(f"Precision@5: {avg_p5:.4f}")
    print(f"MRR:         {mrr:.4f}")
    print(f"Avg Latency: {avg_latency:.2f}ms")
    
    # Check if target met
    if avg_latency < 80:
        print("\nSUCCESS: Performance target (< 80ms) met!")
    else:
        print("\nWARNING: Performance target exceeded.")
        
    db.close()

if __name__ == "__main__":
    run_evaluation()

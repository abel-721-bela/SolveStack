import logging
import time
from sqlalchemy.orm import Session
from database import SessionLocal
from search_service import HybridSearchService
from models import Problem

# Configure logging
logging.basicConfig(level=logging.ERROR) # Lower logging for cleaner output
logger = logging.getLogger(__name__)

# Evaluation Queries and Ground Truth (Relevant IDs)
# These are manually curated based on the 198 problems in the database
EVAL_DATA = [
    {"query": "PostgreSQL pool exhaustion", "relevant_ids": [3]},
    {"query": "JWT auth SPA", "relevant_ids": [4]},
    {"query": "MUI mobile layout", "relevant_ids": [5]},
    {"query": "Docker compose frontend backend", "relevant_ids": [6]},
    {"query": "Firebase security rules", "relevant_ids": [7]},
    {"query": "Axios interceptor JWT", "relevant_ids": [8]},
    {"query": "Python reverse number", "relevant_ids": [175]},
    {"query": "Claude Code CLI auth", "relevant_ids": [11]},
    {"query": "i18n translation support", "relevant_ids": [12, 13, 14, 15, 16]},
    {"query": "Python IndexError list range", "relevant_ids": [176]},
    {"query": "Deno SvelteKit compile error", "relevant_ids": [25]},
    {"query": "Next.js high memory usage", "relevant_ids": [28]},
    {"query": "App router Framer Motion", "relevant_ids": [29]},
    {"query": "Next.js server components debugger", "relevant_ids": [31]},
    {"query": "FlatList scroll items", "relevant_ids": [32]},
    {"query": "Android App Crash tag exists", "relevant_ids": [33]},
    {"query": "Interpolated translateY android jump", "relevant_ids": [35]},
    {"query": "Method Not Allowed POST 405", "relevant_ids": [36]},
    {"query": "GTK Python notified_changed signal", "relevant_ids": [39]},
    {"query": "Restaurant menu print Python", "relevant_ids": [40]},
]

def calculate_metrics(results, relevant_ids):
    """Calculate P@5, R@10, and MRR for a single query."""
    result_ids = [p.ps_id for p in results]
    
    # Precision@5
    top_5 = result_ids[:5]
    p5 = sum(1 for rid in top_5 if rid in relevant_ids) / 5.0
    
    # Recall@10
    top_10 = result_ids[:10]
    found = sum(1 for rid in relevant_ids if rid in top_10)
    r10 = found / len(relevant_ids) if relevant_ids else 0
    
    # MRR (Mean Reciprocal Rank)
    mrr = 0
    for i, rid in enumerate(result_ids):
        if rid in relevant_ids:
            mrr = 1.0 / (i + 1)
            break
            
    return p5, r10, mrr

def run_evaluation():
    db = SessionLocal()
    search_service = HybridSearchService()
    
    # Models to compare
    configs = [
        {"name": "Keyword Only", "weights": (0.0, 1.0, 0.0)},
        {"name": "Semantic Only", "weights": (1.0, 0.0, 0.0)},
        {"name": "Hybrid (0.6/0.3/0.1)", "weights": (0.6, 0.3, 0.1)}
    ]
    
    print("\n" + "="*80)
    print(f"{'Method':<25} | {'P@5':<10} | {'R@10':<10} | {'MRR':<10}")
    print("-" * 80)
    
    summary_results = []

    for config in configs:
        search_service.semantic_weight = config["weights"][0]
        search_service.keyword_weight = config["weights"][1]
        search_service.tag_weight = config["weights"][2]
        
        all_p5, all_r10, all_mrr = [], [], []
        
        for item in EVAL_DATA:
            results = search_service.search(db, query_text=item["query"], limit=max(10, len(item["relevant_ids"])))
            p5, r10, mrr = calculate_metrics(results, item["relevant_ids"])
            all_p5.append(p5)
            all_r10.append(r10)
            all_mrr.append(mrr)
            
        avg_p5 = sum(all_p5) / len(all_p5)
        avg_r10 = sum(all_r10) / len(all_r10)
        avg_mrr = sum(all_mrr) / len(all_mrr)
        
        print(f"{config['name']:<25} | {avg_p5:<10.4f} | {avg_r10:<10.4f} | {avg_mrr:<10.4f}")
        summary_results.append({
            "name": config["name"],
            "p5": avg_p5,
            "r10": avg_r10,
            "mrr": avg_mrr
        })

    print("="*80 + "\n")
    db.close()
    return summary_results

if __name__ == "__main__":
    run_evaluation()

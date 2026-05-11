"""Test all 3 fixes: relevance ranking, difficulty distribution, filter compatibility."""
import requests
import json

BASE = "http://localhost:8000"

def test_search(endpoint, query, label):
    r = requests.get(f"{BASE}/{endpoint}?query={query}&limit=10")
    data = r.json()
    print(f"\n{'='*60}")
    print(f"{label}: '{query}'")
    print(f"  Status: {r.status_code} | Type: {data.get('search_type')} | Results: {data.get('total')}")
    
    if data.get('metadata'):
        print(f"  Metadata: {data['metadata']}")
    
    # Count difficulty distribution
    beginner = intermediate = advanced = 0
    for p in data.get('results', []):
        eis = p.get('engineering_impact_score', 0) or 0
        if eis < 40: beginner += 1
        elif eis <= 70: intermediate += 1
        else: advanced += 1
    
    print(f"  Difficulty mix: Beginner={beginner}, Intermediate={intermediate}, Advanced={advanced}")
    
    for i, p in enumerate(data.get('results', [])[:5], 1):
        eis = p.get('engineering_impact_score', 0) or 0
        diff = "BEG" if eis < 40 else ("INT" if eis <= 70 else "ADV")
        score = p.get('semantic_score', '')
        score_str = f" [sim={score}]" if score else ""
        print(f"    {i}. [{diff} EIS:{eis:.0f}]{score_str} {p['title'][:60]}")

# Test 1: Keyword search - should show relevant results with mixed difficulty
test_search("search/keyword", "docker", "KEYWORD SEARCH")

# Test 2: Semantic search - should use actual cosine similarity now (265 embeddings)
test_search("search/semantic", "docker container deployment", "SEMANTIC SEARCH")

# Test 3: Semantic search for web dev 
test_search("search/semantic", "how to build web applications", "SEMANTIC SEARCH - Web Dev")

# Test 4: Keyword search - python specific
test_search("search/keyword", "python", "KEYWORD SEARCH - Python")

# Test 5: Semantic search - machine learning
test_search("search/semantic", "machine learning model training", "SEMANTIC SEARCH - ML")

print(f"\n{'='*60}")
print("DONE - Check that difficulty is mixed (not all Advanced)")

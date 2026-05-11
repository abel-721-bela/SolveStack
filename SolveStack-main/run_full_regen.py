"""Trigger full regeneration for ALL problems."""
import requests
import time

print("Starting FULL regeneration for all problems...")
print("This will take ~4-5 minutes (1 request/second for ~245 problems)")
print("Using Groq (Gemini was rate-limited)...")
print()

start = time.time()

try:
    r = requests.post(
        "http://localhost:8000/admin/regenerate-explanations?force=true",
        timeout=600  # 10 minute timeout
    )
    
    elapsed = time.time() - start
    
    if r.status_code == 200:
        data = r.json()
        print(f"\nCompleted in {elapsed:.0f}s")
        print(f"Total processed: {data['total_processed']}")
        print(f"Explanations updated: {data['explanations_updated']}")
        print(f"Titles cleaned: {data['titles_cleaned']}")
        print(f"Errors: {data['errors']}")
        print(f"Providers: {data['providers_used']}")
    else:
        print(f"Error: HTTP {r.status_code}")
        print(r.text[:500])
        
except requests.Timeout:
    print(f"Request timed out after {time.time() - start:.0f}s")
except Exception as e:
    print(f"Error: {e}")

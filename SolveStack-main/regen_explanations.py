"""Trigger regeneration of bad humanized explanations via API."""
import requests
import time

print("Triggering regeneration of incomplete/missing explanations...")
print("This calls the backend API which uses Gemini -> Groq -> heuristic fallback.\n")

try:
    r = requests.post(
        "http://localhost:8000/admin/regenerate-explanations",
        params={"limit": 0, "force": False},
        timeout=300  # 5 min timeout for batch processing
    )
    
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Processed: {data.get('total_processed', 0)}")
        print(f"Updated: {data.get('explanations_updated', 0)}")
        print(f"Titles cleaned: {data.get('titles_cleaned', 0)}")
        print(f"Errors: {data.get('errors', 0)}")
        print(f"Providers: {data.get('providers_used', {})}")
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

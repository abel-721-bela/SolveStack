"""Quick check if humanized_explanation comes through API."""
import requests

r = requests.get("http://localhost:8000/problems?limit=3")
data = r.json()
for p in data:
    print(f"ps_id={p['ps_id']}")
    print(f"  title:                {p['title'][:60]}")
    print(f"  humanized_explanation: {repr(p.get('humanized_explanation', 'MISSING_KEY'))[:80]}")
    print()

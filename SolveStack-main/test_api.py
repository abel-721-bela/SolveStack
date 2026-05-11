import requests, json
r = requests.get("http://localhost:8000/problems?limit=2")
data = r.json()
for p in data:
    print(f"Title: {p['title'][:60]}")
    print(f"Humanized: {(p.get('humanized_explanation') or '(empty)')[:60]}")
    print()

"""Test the regeneration endpoint with a small batch."""
import requests, json

print("Testing regeneration with 3 problems...")
r = requests.post("http://localhost:8000/admin/regenerate-explanations?limit=3&force=true")
data = r.json()
print(json.dumps(data, indent=2))

print("\n\nVerifying results...")
r2 = requests.get("http://localhost:8000/problems?limit=3")
for p in r2.json()[:3]:
    print(f"\nTitle: {p['title'][:70]}")
    he = p.get('humanized_explanation', '')
    print(f"Humanized: {he[:100] if he else '(empty)'}")

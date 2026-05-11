import requests
r = requests.get("http://localhost:8000/problems/261")
data = r.json()
print(f"Title: {data['title']}")
print(f"humanized_explanation: {data.get('humanized_explanation', 'MISSING')}")
print(f"description (first 100): {data.get('description', '')[:100]}")

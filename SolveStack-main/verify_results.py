"""Verify the regeneration results."""
import requests

print("=== VERIFICATION ===\n")

# 1. Check a sample of problems via API
r = requests.get("http://localhost:8000/problems?limit=10")
data = r.json()

empty_count = 0
title_copy_count = 0

for p in data:
    title = p.get('title', '')
    he = p.get('humanized_explanation', '')
    
    if not he or not he.strip():
        empty_count += 1
    elif he.lower().startswith(title.lower()[:30]):
        title_copy_count += 1
    
    print(f"ID {p['ps_id']}:")
    print(f"  Title:     {title[:70]}")
    print(f"  Humanized: {he[:100] if he else '(EMPTY!)'}")
    
    # Check for HTML entities in title
    if '&quot;' in title or '&amp;' in title or '&#' in title:
        print(f"  WARNING: Title still has HTML entities!")
    print()

# 2. Check the full DB
from database import engine
from sqlalchemy import text
conn = engine.connect()

total = conn.execute(text("SELECT COUNT(*) FROM problems")).scalar()
filled = conn.execute(text(
    "SELECT COUNT(*) FROM problems WHERE humanized_explanation IS NOT NULL AND humanized_explanation != ''"
)).scalar()
same_title = conn.execute(text(
    "SELECT COUNT(*) FROM problems WHERE humanized_explanation LIKE title || '%'"
)).scalar()
has_entities = conn.execute(text(
    "SELECT COUNT(*) FROM problems WHERE title LIKE '%&quot;%' OR title LIKE '%&amp;%' OR title LIKE '%&#%'"
)).scalar()

print(f"\n=== DATABASE SUMMARY ===")
print(f"Total problems: {total}")
print(f"With humanized_explanation: {filled} ({filled/total*100:.0f}%)")
print(f"Explanation = title copy: {same_title}")
print(f"Titles with HTML entities: {has_entities}")
conn.close()

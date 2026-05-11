"""Audit humanized_explanation quality from the DB."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import engine
from sqlalchemy import text

conn = engine.connect()
rows = conn.execute(text(
    "SELECT ps_id, title, humanized_explanation, description FROM problems ORDER BY ps_id"
)).fetchall()

print(f"Total: {len(rows)}\n")

empty = 0
incomplete = 0
same_as_title = 0
too_short = 0
total_with_he = 0

examples_incomplete = []
examples_same = []
examples_short = []

for row in rows:
    ps_id, title, he, desc = row
    title = (title or "").strip()
    he = (he or "").strip()
    
    if not he or len(he) < 10:
        empty += 1
        continue
    
    total_with_he += 1
    
    # Incomplete: ends abruptly without proper punctuation
    if he[-1] not in '.!?)\'"':
        incomplete += 1
        if len(examples_incomplete) < 10:
            examples_incomplete.append((ps_id, title[:50], he))
    
    # Same as title
    if he.lower().strip() == title.lower().strip():
        same_as_title += 1
        if len(examples_same) < 5:
            examples_same.append((ps_id, title[:50], he[:50]))
    
    # Too short to be useful
    if len(he) < 40:
        too_short += 1
        if len(examples_short) < 5:
            examples_short.append((ps_id, he))

print(f"With humanized_explanation: {total_with_he}")
print(f"Empty/missing: {empty}")
print(f"Incomplete (no ending punct): {incomplete}")
print(f"Same as title: {same_as_title}")
print(f"Too short (<40 chars): {too_short}")

needs_regen = empty + incomplete + same_as_title
print(f"\n==> NEEDS REGENERATION: {needs_regen}")

print(f"\n{'='*80}")
print("INCOMPLETE EXAMPLES (last 100 chars):")
print(f"{'='*80}")
for ps_id, title, he in examples_incomplete:
    safe_he = he.encode('ascii', errors='replace').decode('ascii')
    print(f"\n  PS#{ps_id}: {title}")
    print(f"    HE: {safe_he[-120:]}")

if examples_same:
    print(f"\n{'='*80}")
    print("SAME AS TITLE:")
    print(f"{'='*80}")
    for ps_id, t, h in examples_same:
        print(f"  PS#{ps_id}: {t}")

conn.close()

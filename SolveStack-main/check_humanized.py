from database import engine
from sqlalchemy import text

conn = engine.connect()

# Check if column exists
result = conn.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='problems' AND column_name='humanized_explanation'"
))
rows = result.fetchall()
print(f"humanized_explanation column exists: {len(rows) > 0}")

if len(rows) > 0:
    # Sample some data
    result2 = conn.execute(text("SELECT ps_id, title, humanized_explanation FROM problems LIMIT 5"))
    for row in result2:
        t = (row[1] or "")[:80]
        h = (row[2] or "")[:80]
        print(f"  ID {row[0]}:")
        print(f"    Title:     {t}")
        print(f"    Humanized: {h}")
        print()

    # Check how many have humanized = title or similar
    result3 = conn.execute(text(
        "SELECT COUNT(*) FROM problems WHERE humanized_explanation IS NOT NULL AND humanized_explanation != ''"
    ))
    filled = result3.scalar()
    
    result4 = conn.execute(text("SELECT COUNT(*) FROM problems"))
    total = result4.scalar()
    
    print(f"Total problems: {total}")
    print(f"With humanized_explanation filled: {filled}")
    
    # Check how many have humanized = title prefix
    result5 = conn.execute(text(
        "SELECT COUNT(*) FROM problems WHERE humanized_explanation LIKE title || '%'"
    ))
    same_as_title = result5.scalar()
    print(f"humanized_explanation starts with title: {same_as_title}")

conn.close()

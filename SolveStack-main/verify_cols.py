from database import engine
from sqlalchemy import text
conn = engine.connect()
r = conn.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='problems' AND column_name IN "
    "('is_gibberish','is_technical','humanized_explanation','solution_possibility')"
))
cols = [row[0] for row in r.fetchall()]
print(f"Verified columns: {cols}")
print(f"All 4 present: {len(cols) == 4}")
conn.close()

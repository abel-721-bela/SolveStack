"""Force regenerate specific problems."""
from database import engine
from sqlalchemy import text

print("Finding the empty one...")
conn = engine.connect()
rows = conn.execute(text("SELECT ps_id FROM problems WHERE humanized_explanation IS NULL OR humanized_explanation = ''")).fetchall()
print(f"Empty rows: {rows}")
conn.close()

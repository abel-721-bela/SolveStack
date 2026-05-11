from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        print("RESULT:", conn.execute(text("SELECT 1")).scalar())
except Exception as e:
    print("ERROR:", e)

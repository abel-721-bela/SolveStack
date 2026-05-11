"""Check DB search readiness."""
from database import engine
from sqlalchemy import text

conn = engine.connect()
total = conn.execute(text("SELECT COUNT(*) FROM problems")).scalar()
with_emb = conn.execute(text("SELECT COUNT(*) FROM problems WHERE embedding IS NOT NULL")).scalar()

# Check if search_vector column exists
try:
    with_sv = conn.execute(text("SELECT COUNT(*) FROM problems WHERE search_vector IS NOT NULL")).scalar()
except Exception as e:
    with_sv = f"ERROR: {e}"

# Check if vector extension is available
try:
    ext = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
    vec_ext = ext[0] if ext else "NOT INSTALLED"
except:
    vec_ext = "CHECK FAILED"

print(f"Total problems: {total}")
print(f"With embeddings: {with_emb}")
print(f"With search_vector: {with_sv}")
print(f"pgvector extension: {vec_ext}")
conn.close()

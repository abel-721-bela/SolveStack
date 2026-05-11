"""
Generate embeddings for ALL problems that don't have them yet.
Uses SentenceTransformer (all-MiniLM-L6-v2) to create 384-dim normalized vectors.
Stores embeddings as JSON arrays in the embedding column.
"""
import sys
import json
import time
from database import engine
from sqlalchemy import text
from embedding_service import get_embedding_service

print("=" * 60)
print("BATCH EMBEDDING GENERATION")
print("=" * 60)

embedding_service = get_embedding_service()

conn = engine.connect()

# Get all problems without embeddings
rows = conn.execute(text(
    "SELECT ps_id, title, description, suggested_tech FROM problems WHERE embedding IS NULL ORDER BY ps_id"
)).fetchall()

print(f"\nProblems without embeddings: {len(rows)}")
if len(rows) == 0:
    print("All problems already have embeddings!")
    conn.close()
    sys.exit(0)

# Also count existing
existing = conn.execute(text("SELECT COUNT(*) FROM problems WHERE embedding IS NOT NULL")).scalar()
print(f"Already have embeddings: {existing}")
print(f"\nGenerating embeddings for {len(rows)} problems...\n")

success = 0
errors = 0
batch_size = 10

for i, row in enumerate(rows, 1):
    ps_id = row[0]
    title = row[1] or ""
    description = row[2] or ""
    tech = row[3] or ""
    
    try:
        # Build text for embedding (same format as generate_embedding)
        text_input = f"Title: {title.strip()}. Description: {description.strip()[:300]}. Tags: {tech}"
        if len(text_input) > 500:
            text_input = text_input[:500]
        
        # Generate embedding
        embedding = embedding_service._model.encode(text_input, normalize_embeddings=True).tolist()
        
        # Store as JSON array (compatible with both pgvector Vector and JSON column types)
        emb_json = json.dumps(embedding)
        
        conn.execute(
            text("UPDATE problems SET embedding = :emb WHERE ps_id = :ps_id"),
            {"emb": emb_json, "ps_id": ps_id}
        )
        conn.commit()
        
        success += 1
        if i % batch_size == 0 or i == len(rows):
            print(f"  [{i}/{len(rows)}] Generated {success} embeddings ({errors} errors)")
        
    except Exception as e:
        errors += 1
        print(f"  [{i}/{len(rows)}] ERROR ps_id={ps_id}: {type(e).__name__}: {str(e)[:80]}")
        try:
            conn.rollback()
        except:
            pass
        continue

conn.close()

print(f"\n{'=' * 60}")
print(f"COMPLETE: {success} embeddings generated, {errors} errors")
print(f"Total with embeddings now: {existing + success}")
print(f"{'=' * 60}")

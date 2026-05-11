from database import engine
from sqlalchemy import text

def verify():
    with engine.connect() as conn:
        # Check pgvector extension
        res = conn.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")).scalar()
        print(f"pgvector extension: {'[OK]' if res else '[MISSING]'}")

        # Check search_vector population
        res_search = conn.execute(text("SELECT count(*) FROM problems WHERE search_vector IS NOT NULL")).scalar()
        # Check embedding population
        res_embedding = conn.execute(text("SELECT count(*) FROM problems WHERE embedding IS NOT NULL")).scalar()
        total = conn.execute(text("SELECT count(*) FROM problems")).scalar()
        print(f"Problems with search_vector: {res_search}/{total}")
        print(f"Problems with embedding: {res_embedding}/{total}")

        # Check columns types
        res = conn.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'problems' AND column_name IN ('embedding', 'search_vector')
        """)).fetchall()
        for row in res:
            print(f"Column: {row[0]} | Type: {row[1]} | UDT: {row[2]}")

        # Check indices
        res = conn.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'problems' AND indexname IN ('problems_search_idx', 'problems_embedding_idx')
        """)).fetchall()
        for row in res:
            print(f"Index: {row[0]} | Definition: {row[1]}")

if __name__ == "__main__":
    verify()

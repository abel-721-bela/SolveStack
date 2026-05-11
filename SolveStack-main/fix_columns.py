"""Add missing columns to the problems table in PostgreSQL."""
from database import engine
from sqlalchemy import text

conn = engine.connect()

# Check what columns exist
result = conn.execute(text(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='problems' ORDER BY ordinal_position"
))
existing_columns = [row[0] for row in result.fetchall()]
print(f"Existing columns ({len(existing_columns)}):")
for col in existing_columns:
    print(f"  - {col}")

# Columns we need that might be missing
needed_columns = {
    "is_gibberish": "BOOLEAN DEFAULT FALSE",
    "is_technical": "BOOLEAN DEFAULT TRUE",
    "humanized_explanation": "TEXT",
    "solution_possibility": "VARCHAR(50)",
}

print(f"\nChecking for missing columns...")
for col_name, col_type in needed_columns.items():
    if col_name not in existing_columns:
        print(f"  Adding missing column: {col_name} ({col_type})")
        conn.execute(text(f"ALTER TABLE problems ADD COLUMN {col_name} {col_type}"))
        conn.commit()
    else:
        print(f"  ✓ {col_name} already exists")

print("\nDone! All columns verified.")
conn.close()

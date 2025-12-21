"""
Quick script to test PostgreSQL connection and create tables.
Run this instead of Alembic migration.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("PostgreSQL Connection Test")
print("=" * 60)

# Check environment variable
db_url = os.getenv("DATABASE_URL")
print(f"\n1. DATABASE_URL from .env: {db_url}")

if not db_url:
    print("   ❌ DATABASE_URL not set!")
    print("   → Add to .env file: DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack")
else:
    print("   ✅ DATABASE_URL loaded")

# Check database engine
from database import engine

print(f"\n2. Database Engine URL: {engine.url}")

if "sqlite" in str(engine.url):
    print("   ❌ Still using SQLite!")
    print("   → Check if .env file exists and has DATABASE_URL")
elif "postgresql" in str(engine.url):
    print("   ✅ Using PostgreSQL!")
else:
    print(f"   ⚠️ Unknown database: {engine.url}")

# Try to create tables
if "postgresql" in str(engine.url):
    try:
        from models import Base
        
        print("\n3. Creating tables in PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ All tables created successfully!")
        
        # List tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n4. Tables in database ({len(tables)}):")
        for table in sorted(tables):
            print(f"   - {table}")
        
        print("\n" + "=" * 60)
        print("✅ PostgreSQL setup complete!")
        print("=" * 60)
        print("\nNext: Restart uvicorn and test at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        print("\n   Possible issues:")
        print("   - PostgreSQL not running")
        print("   - Database 'solvestack' doesn't exist")
        print("   - Wrong credentials")
else:
    print("\n⚠️ Skipping table creation - not connected to PostgreSQL")
    print("\nFix DATABASE_URL first, then run this script again.")

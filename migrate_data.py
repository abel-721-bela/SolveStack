"""
Data migration script: SQLite to PostgreSQL

This script migrates existing problems from problems.db (SQLite) to PostgreSQL.
Run this ONCE after setting up PostgreSQL database.

Usage:
    python migrate_data.py
"""

import sqlite3
import json
from sqlalchemy.orm import Session
from models import Base, Problem
from database import engine, SessionLocal

def migrate_sqlite_to_postgres():
    """Migrate all problems from SQLite to PostgreSQL"""
    
    # Create all tables in PostgreSQL
    print("Creating PostgreSQL tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    # Connect to SQLite
    print("\nConnecting to SQLite database...")
    sqlite_conn = sqlite3.connect('problems.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get all problems from SQLite
    try:
        sqlite_cursor.execute("SELECT * FROM problem_statements")
        sqlite_problems = sqlite_cursor.fetchall()
        print(f"✓ Found {len(sqlite_problems)} problems in SQLite")
    except sqlite3.OperationalError as e:
        print(f"Error: Could not read from SQLite database. Make sure problems.db exists.")
        print(f"Error details: {e}")
        sqlite_conn.close()
        return
    
    # Get column names
    sqlite_cursor.execute("PRAGMA table_info(problem_statements)")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    print(f"✓ SQLite columns: {columns}")
    
    # Insert into PostgreSQL using ORM
    print("\nMigrating to PostgreSQL...")
    db: Session = SessionLocal()
    
    inserted = 0
    skipped = 0
    
    for row in sqlite_problems:
        # Create dictionary from row
        problem_dict = dict(zip(columns, row))
        
        # Parse tags if it's a JSON string
        if 'tags' in problem_dict and isinstance(problem_dict['tags'], str):
            try:
                problem_dict['tags'] = json.loads(problem_dict['tags']) if problem_dict['tags'] else []
            except:
                problem_dict['tags'] = []
        
        # Remove ps_id to let PostgreSQL auto-generate it
        if 'ps_id' in problem_dict:
            del problem_dict['ps_id']
        
        try:
            new_problem = Problem(**problem_dict)
            db.add(new_problem)
            db.commit()
            inserted += 1
            print(f"✓ Migrated: {problem_dict['title'][:50]}...")
        except Exception as e:
            db.rollback()
            skipped += 1
            print(f"✗ Skipped (duplicate?): {problem_dict.get('title', 'Unknown')[:50]}...")
    
    db.close()
    sqlite_conn.close()
    
    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"{'='*60}")
    print(f"✓ Inserted: {inserted} problems")
    print(f"✗ Skipped: {skipped} problems (duplicates)")
    print(f"\nYou can now use the PostgreSQL database with main.py")

if __name__ == "__main__":
    print("="*60)
    print("SQLite to PostgreSQL Migration Tool")
    print("="*60)
    print("\nIMPORTANT: Make sure you have:")
    print("1. PostgreSQL installed and running")
    print("2. Created .env file with DATABASE_URL")
    print("3. Installed requirements: pip install -r requirements.txt")
    print("\n" + "="*60)
    
    response = input("\nReady to migrate? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_sqlite_to_postgres()
    else:
        print("Migration cancelled.")

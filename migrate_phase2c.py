"""
Quick migration script for Phase 2C database columns.
Run this to add new columns to existing SQLite database.
"""

from database import engine

def migrate_database():
    """Add Phase 2C columns to existing database."""
    conn = engine.raw_connection()
    cursor = conn.cursor()
    
    print("🔧 Migrating database for Phase 2C...")
    
    try:
        # User columns
        print("Adding User columns...")
        cursor.execute('ALTER TABLE users ADD COLUMN skills TEXT DEFAULT "[]"')
        cursor.execute('ALTER TABLE users ADD COLUMN experience_level TEXT DEFAULT "Intermediate"')
        cursor.execute('ALTER TABLE users ADD COLUMN interests TEXT DEFAULT "[]"')
        cursor.execute('ALTER TABLE users ADD COLUMN activity_score INTEGER DEFAULT 50')
        cursor.execute('ALTER TABLE users ADD COLUMN preferred_difficulty TEXT DEFAULT "Intermediate"')
        cursor.execute('ALTER TABLE users ADD COLUMN preferred_effort TEXT DEFAULT "1-3 days"')
        
        # Problem columns
        print("Adding Problem columns...")
        cursor.execute('ALTER TABLE problems ADD COLUMN quality_score INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE problems ADD COLUMN difficulty TEXT DEFAULT "Intermediate"')
        cursor.execute('ALTER TABLE problems ADD COLUMN estimated_effort TEXT DEFAULT "1-3 days"')
        cursor.execute('ALTER TABLE problems ADD COLUMN upvotes INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE problems ADD COLUMN views INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE problems ADD COLUMN score_updated_at TEXT')
        
        conn.commit()
        print('✅ Database migrated successfully!')
        
    except Exception as e:
        error_msg = str(e)
        if 'duplicate column' in error_msg.lower():
            print('⚠️ Columns already exist (migration previously completed)')
        else:
            print(f'❌ Migration error: {e}')
            raise
    finally:
        conn.close()


def setup_sample_data():
    """Run the setup script to populate sample data."""
    import subprocess
    import sys
    
    print("\n📊 Setting up sample data...")
    result = subprocess.run([sys.executable, 'setup_phase2c_data.py'])
    
    if result.returncode == 0:
        print("\n✅ All done! Phase 2C is ready to test.")
    else:
        print("\n⚠️ Sample data setup had issues. You can still test the endpoints.")


if __name__ == "__main__":
    migrate_database()
    setup_sample_data()
    
    print("\n" + "="*60)
    print("🎉 Phase 2C Setup Complete!")
    print("="*60)
    print("\n📖 Test the new endpoints:")
    print("   1. Open http://localhost:8000/docs")
    print("   2. Look for 'Phase 2C' sections")
    print("   3. Try POST /problems/1/score")
    print("   4. Try GET /recommendations (need to login first)")
    print("\n💡 See PHASE2C_TESTING.md for detailed instructions")

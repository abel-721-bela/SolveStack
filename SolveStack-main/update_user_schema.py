from database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    with engine.connect() as conn:
        print("Adding columns to users table...")
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS skills JSONB DEFAULT '[]'::jsonb"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS interests JSONB DEFAULT '[]'::jsonb"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS activity_score INTEGER DEFAULT 0"))
            conn.commit()
            print("Successfully updated users table schema.")
        except Exception as e:
            print(f"Error updating users table: {e}")

if __name__ == "__main__":
    update_schema()

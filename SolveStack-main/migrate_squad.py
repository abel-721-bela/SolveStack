from database import engine
from sqlalchemy import text

with engine.begin() as conn: # engine.begin auto commits
    conn.execute(text("ALTER TABLE collaboration_groups ADD COLUMN name VARCHAR"))
    conn.execute(text("ALTER TABLE collaboration_groups ADD COLUMN description VARCHAR"))
    conn.execute(text("ALTER TABLE collaboration_groups ADD COLUMN leader_id INTEGER REFERENCES users(id)"))
print('Migration complete')

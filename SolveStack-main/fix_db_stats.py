from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
import os

DB_URL = "sqlite:///./solvestack.db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_user_stats():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            updated = False
            if user.activity_score is None:
                user.activity_score = 50
                updated = True
            if not user.skills:
                user.skills = []
                updated = True
            if not user.interests:
                user.interests = []
                updated = True
            
            if updated:
                print(f"Updating user {user.username}")
                db.add(user)
        
        db.commit()
        print("Database stats cleanup complete.")
                
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_stats()

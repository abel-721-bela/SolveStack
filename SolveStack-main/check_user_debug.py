from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Problem
import os

DB_URL = "sqlite:///./solvestack.db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_user_data():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"--- USER DEBUG INFO ---")
        print(f"Total Users Found: {len(users)}")
        for user in users:
            print(f"\n[USER] ID: {user.id} | Username: {user.username} | Email: {user.email}")
            print(f"  - Pulse (Activity Score): {user.activity_score}")
            print(f"  - Interests Count: {len(user.interested_problems)}")
            for idx, p in enumerate(user.interested_problems, 1):
                print(f"    {idx}. {p.title[:50]} (ID: {p.ps_id})")
            
            try:
                print(f"  - Squads Count: {len(user.joined_collaboration_groups)}")
            except Exception as e:
                print(f"  - Squads Count: Error checking ({str(e)})")
        print(f"\n--- END DEBUG INFO ---")
                
    finally:
        db.close()

if __name__ == "__main__":
    debug_user_data()

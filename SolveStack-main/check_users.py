from database import SessionLocal
from models import User
import json

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for u in users:
            print(f"User: {u.username}")
            print(f"  Skills: {u.skills}")
            print(f"  Interests: {u.interests}")
            print(f"  Activity Score: {u.activity_score}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()

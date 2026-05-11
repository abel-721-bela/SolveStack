from database import SessionLocal
from models import User
import json

def seed_user_data():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for u in users:
            if u.username == "joe":
                u.skills = ["Python", "FastAPI", "PostgreSQL", "React", "Docker"]
                u.interests = ["Scalable Architecture", "Open Source Software", "Real-time Systems"]
                u.activity_score = 85
            elif u.username == "testuser":
                u.skills = ["Node.js", "TypeScript", "AWS", "Kubernetes", "Redis"]
                u.interests = ["Distributed Systems", "Cloud Native", "DevOps Automation"]
                u.activity_score = 92
        db.commit()
        print("Successfully seeded user mock data.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_user_data()

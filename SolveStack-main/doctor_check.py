import sys
import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from main import app, SearchService
from database import SessionLocal
from models import User, Problem, problem_interests

def diagnostic():
    db = SessionLocal()
    print("--- SYSTEM DIAGNOSTIC ---")
    
    # 1. Check User 5
    user = db.query(User).filter(User.id == 5).first()
    if not user:
        print("Error: User 5 not found in DB")
    else:
        print(f"User 5 Found: {user.username} ({user.email})")
        
        # Test count logic exactly as in main.py
        interested_count = db.query(func.count(problem_interests.c.user_id)).filter(
            problem_interests.c.user_id == user.id
        ).scalar() or 0
        print(f"DB Interest Count for User 5: {interested_count}")
        
        # Test serialization of skills/interests
        print(f"Raw Skills: {user.skills} (Type: {type(user.skills)})")
        print(f"Raw Interests: {user.interests} (Type: {type(user.interests)})")

    # 2. Test Search Fallback
    test_query = "Next.js navigation"
    all_probs = db.query(Problem).all()
    print(f"Total problems in shelf: {len(all_probs)}")
    
    results = SearchService.get_semantic_matches(test_query, all_probs)
    print(f"Search results for '{test_query}': {results}")

    # 3. Environment Check
    try:
        import sklearn
        print(f"Sklearn Version: {sklearn.__version__}")
    except ImportError:
        print("Sklearn STATUS: Missing")

    db.close()

if __name__ == "__main__":
    diagnostic()

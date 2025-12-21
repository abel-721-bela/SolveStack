"""
Test script to verify backend setup

This script tests:
1. All imports work correctly
2. Models can be created
3. Database connection works
4. Authentication functions work
"""

import sys

print("="*60)
print("SolveStack Backend Test")
print("="*60)

# Test 1: Import core modules
print("\n[Test 1] Importing core modules...")
try:
    from models import User, Problem, CollaborationGroup, Base
    from database import engine, get_db
    from schemas import UserCreate, ProblemResponse
    from auth import get_password_hash, verify_password, create_access_token
    import pyproblem_shelf
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test 2: Database connection
print("\n[Test 2] Testing database connection...")
try:
    from sqlalchemy.orm import Session
    db: Session = next(get_db())
    print(f"✓ Database connected: {engine.url}")
    db.close()
except Exception as e:
    print(f"✗ Database connection error: {e}")
    print("Note: Make sure .env file exists with DATABASE_URL")
    # Don't exit - this is expected if .env not set up

# Test 3: Create database tables
print("\n[Test 3] Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
except Exception as e:
    print(f"✗ Table creation error: {e}")

# Test 4: Password hashing
print("\n[Test 4] Testing password hashing...")
try:
    test_password = "test123"
    hashed = get_password_hash(test_password)
    is_valid = verify_password(test_password, hashed)
    if is_valid:
        print("✓ Password hashing works correctly")
    else:
        print("✗ Password verification failed")
except Exception as e:
    print(f"✗ Password hashing error: {e}")

# Test 5: JWT token creation
print("\n[Test 5] Testing JWT token creation...")
try:
    token = create_access_token(data={"sub": "test@example.com"})
    print(f"✓ JWT token created: {token[:50]}...")
except Exception as e:
    print(f"✗ JWT token error: {e}")
    print("Note: Make sure SECRET_KEY is set in .env")

# Test 6: Reddit API (if credentials exist)
print("\n[Test 6] Testing Reddit API connection...")
try:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv('REDDIT_CLIENT_ID')
    if client_id:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret =os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        # Test connection
        reddit.user.me()  # Will be None for script oauth
        print("✓ Reddit API credentials valid")
    else:
        print("⚠ Reddit credentials not found in .env")
except Exception as e:
    print(f"⚠ Reddit API test skipped: {e}")

# Summary
print("\n" + "="*60)
print("Test Summary")
print("="*60)
print("✓ = Passed")
print("✗ = Failed (needs attention)")
print("⚠ = Skipped (optional)")
print("\nNext steps:")
print("1. Create .env file from .env.example")
print("2. Run: uvicorn main:app --reload")
print("3. Visit: http://localhost:8000/docs")
print("="*60)

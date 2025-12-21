"""
Auto-fix .env file to use PostgreSQL.
This script will replace SQLite DATABASE_URL with PostgreSQL.
"""

import os
import re

env_file = ".env"

print("=" * 60)
print("Auto-Fixing .env File for PostgreSQL")
print("=" * 60)

# Check if .env exists
if not os.path.exists(env_file):
    print(f"\n❌ {env_file} doesn't exist!")
    print("Creating new .env file...")
    
    content = """# SolveStack Environment - PostgreSQL Mode
DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack
SECRET_KEY=dev-secret-key-change-later
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=SolveStack/1.0
GITHUB_TOKEN=your_github_token
FIREBASE_CREDENTIALS_PATH=path/to/firebase-service-account.json
"""
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Created {env_file} with PostgreSQL configuration")
else:
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    print(f"\n📄 Current {env_file} content:")
    print("-" * 60)
    print(content)
    print("-" * 60)
    
    # Check for DATABASE_URL
    if "DATABASE_URL" in content:
        # Replace any DATABASE_URL line with PostgreSQL version
        new_content = re.sub(
            r'DATABASE_URL\s*=\s*.*',
            'DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack',
            content
        )
        
        # Write back
        with open(env_file, 'w') as f:
            f.write(new_content)
        
        print("\n✅ Fixed DATABASE_URL to use PostgreSQL")
    else:
        # Add DATABASE_URL at the top
        new_content = "DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack\n" + content
        
        with open(env_file, 'w') as f:
            f.write(new_content)
        
        print("\n✅ Added DATABASE_URL for PostgreSQL")
    
    print("\n📄 New .env content:")
    print("-" * 60)
    print(new_content)
    print("-" * 60)

# Verify it worked
print("\n🔍 Verifying fix...")
from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload

db_url = os.getenv("DATABASE_URL")
print(f"\nDATABASE_URL now: {db_url}")

if db_url and "postgresql" in db_url:
    print("✅ SUCCESS! .env file fixed!")
    print("\nNext steps:")
    print("1. Run: python test_pg_connection.py")
    print("2. Restart uvicorn")
else:
    print("❌ Still not working. DATABASE_URL:", db_url)
    print("\nTry manually editing .env file:")
    print("Open .env in VSCode and set:")
    print("DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack")

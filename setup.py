"""
Quick setup script for SolveStack backend
This will help you create the .env file and test the setup
"""

import os
import secrets

print("=" * 60)
print("SolveStack Backend Quick Setup")
print("=" * 60)

# Check if .env already exists
if os.path.exists('.env'):
    print("\n⚠️  .env file already exists!")
    response = input("Do you want to overwrite it? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Setup cancelled. Using existing .env file.")
        print("\nYou can now run: uvicorn main:app --reload")
        exit(0)

print("\n📝 Creating .env file...")
print("\nI'll ask you a few questions to set up your environment.\n")

# Get Reddit credentials (already known from .env.example)
print("=" * 60)
print("Reddit API Credentials")
print("=" * 60)
reddit_id = input("Reddit Client ID [pcmuYOAa8SuLtpAyUqQHfg]: ").strip() or "pcmuYOAa8SuLtpAyUqQHfg"
reddit_secret = input("Reddit Client Secret [RXndXBRDFimFf1XjTSc0TSfCc8tGEg]: ").strip() or "RXndXBRDFimFf1XjTSc0TSfCc8tGEg"
reddit_agent = input("Reddit User Agent [platform:MyOwnBot:1.0 (by /u/New_Cat6293)]: ").strip() or "platform:MyOwnBot:1.0 (by /u/New_Cat6293)"

# Database choice
print("\n" + "=" * 60)
print("Database Configuration")
print("=" * 60)
print("Choose database:")
print("1. SQLite (easiest - no setup needed)")
print("2. PostgreSQL (production-ready)")
db_choice = input("\nEnter choice [1]: ").strip() or "1"

if db_choice == "2":
    print("\nEnter PostgreSQL connection details:")
    pg_user = input("  Username [postgres]: ").strip() or "postgres"
    pg_pass = input("  Password: ").strip() or "password"
    pg_host = input("  Host [localhost]: ").strip() or "localhost"
    pg_port = input("  Port [5432]: ").strip() or "5432"
    pg_db = input("  Database name [solvestack]: ").strip() or "solvestack"
    database_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
else:
    database_url = "sqlite:///./problems.db"
    print(f"✓ Using SQLite: {database_url}")

# Generate secret key
print("\n" + "=" * 60)
print("Security Configuration")
print("=" * 60)
secret_key = secrets.token_urlsafe(32)
print(f"✓ Generated secure SECRET_KEY: {secret_key[:20]}...")

# Optional fields
print("\n" + "=" * 60)
print("Optional Configuration (press Enter to skip)")
print("=" * 60)
github_token = input("GitHub API Token (for higher rate limits): ").strip()
stripe_secret = input("Stripe Secret Key: ").strip()
stripe_public = input("Stripe Publishable Key: ").strip()
stripe_price = input("Stripe Price ID: ").strip()

# Create .env content
env_content = f"""# SolveStack Environment Configuration
# Generated on: {os.popen('date /t').read().strip()}

# ============================================
# Reddit API Credentials
# ============================================
REDDIT_CLIENT_ID={reddit_id}
REDDIT_CLIENT_SECRET={reddit_secret}
REDDIT_USER_AGENT={reddit_agent}

# ============================================
# Database Configuration
# ============================================
DATABASE_URL={database_url}

# ============================================
# JWT Authentication
# ============================================
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# Stripe Payment Integration (Optional)
# ============================================
STRIPE_SECRET_KEY={stripe_secret}
STRIPE_PUBLISHABLE_KEY={stripe_public}
STRIPE_PRICE_ID={stripe_price}

# ============================================
# GitHub API (Optional)
# ============================================
GITHUB_TOKEN={github_token}
"""

# Write .env file
with open('.env', 'w') as f:
    f.write(env_content)

print("\n" + "=" * 60)
print("✅ Setup Complete!")
print("=" * 60)
print(f"\n✓ Created .env file")
print(f"✓ Database: {database_url}")
print(f"✓ Secret key generated")

print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)
print("\n1. Start the FastAPI server:")
print("   uvicorn main:app --reload")
print("\n2. Open your browser:")
print("   http://localhost:8000/docs")
print("\n3. Try the API:")
print("   - POST /register to create a user")
print("   - POST /login to get a JWT token")
print("   - GET /problems to see scraped problems")
print("\n" + "=" * 60)

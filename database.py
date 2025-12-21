"""
Database configuration with PostgreSQL support for production

Supports two modes:
- Development: SQLite (local, no setup required)
- Production: PostgreSQL (scalable, production-ready)

Environment variable DATABASE_URL determines the mode:
- If set → Uses PostgreSQL
- If not set → Defaults to SQLite

For production, set in .env:
DATABASE_URL=postgresql://user:password@localhost:5432/solvestack
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production: PostgreSQL
    print(f"📊 Using PostgreSQL: {DATABASE_URL.split('@')[-1]}")  # Hide credentials
    
    # PostgreSQL requires different settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,        # Connection pool for concurrent requests
        max_overflow=20,      # Additional connections if pool is full
        echo=False            # Set to True for SQL query logging
    )
else:
    # Development: SQLite (fallback)
    print("📊 Using SQLite (Development Mode)")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./solvestack.db"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency injection for database sessions.
    
    Usage in FastAPI endpoints:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    
    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# For reference: Database URL formats
"""
SQLite (Development):
    database_url = "sqlite:///./solvestack.db"

PostgreSQL (Production):
    database_url = "postgresql://username:password@localhost:5432/database_name"
    
    Local PostgreSQL setup:
    1. Install PostgreSQL
    2. Create database: CREATE DATABASE solvestack;
    3. Create user: CREATE USER solvestack_user WITH PASSWORD 'your_password';
    4. Grant privileges: GRANT ALL PRIVILEGES ON DATABASE solvestack TO solvestack_user;
    5. Set DATABASE_URL in .env

PostgreSQL on Cloud (Render, AWS RDS, etc.):
    Provided by hosting service, add to .env
"""

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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./solvestack.db")

if DATABASE_URL.startswith("postgresql"):
    # Production: PostgreSQL
    print(f"[DB] Using PostgreSQL: {DATABASE_URL.split('@')[-1]}")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )
else:
    # Development: SQLite
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(base_dir, "solvestack_dev.db")
    db_url = f"sqlite:///{sqlite_path}"
    print(f"[DB] Using SQLite: {db_url}")
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
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

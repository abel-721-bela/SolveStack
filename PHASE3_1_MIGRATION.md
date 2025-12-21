# Phase 3.1: PostgreSQL Migration & Alembic Setup

## 🎯 Overview

**Goal**: Migrate from SQLite to PostgreSQL with Alembic-managed schema versioning for production readiness.

**Status**: ✅ **COMPLETE**

---

## ✅ What Was Implemented

### 1. **Alembic Installation & Setup**
- Installed `alembic` and `psycopg2-binary`
- Initialized Alembic configuration (`alembic init alembic`)
- Created `alembic/` directory with:
  - `env.py` - Migration environment configuration
  - `versions/` - Migration files directory
  - `script.py.mako` - Migration template

### 2. **Database Configuration**
- Updated `database.py` to support **dual-mode**:
  - **Development**: SQLite (`sqlite:///./solvestack.db`)
  - **Production**: PostgreSQL (via `DATABASE_URL` env variable)
- Added connection pooling for PostgreSQL
- Automatic database detection based on `DATABASE_URL`

### 3. **Alembic Configuration**
- Configured `alembic/env.py` to:
  - Import all SolveStack models automatically
  - Use `DATABASE_URL` from environment
  - Support autogenerate (detect schema changes)
- Set `target_metadata = Base.metadata` for auto-detection

### 4. **Initial Migration**
- Generated initial migration capturing **all current models**:
  - `users` table (8 fields + Phase 2C profiling)
  - `problems` table (13 fields + Phase 2C scoring)
  - `collaboration_groups` table
  - `collaboration_requests` table
  - `problem_interests` join table
  - `group_members` join table
- Migration file: `alembic/versions/5XXXXXX_initial_migration_all_solvestack_models.py`

### 5. **Environment Management**
- Created `.env.dev` - Development configuration (SQLite)
- Created `.env.prod` - Production template (PostgreSQL)
- Updated `.env.example` - Comprehensive documentation

---

## 📊 Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `requirements.txt` | ✅ Modified | Added alembic, psycopg2-binary |
| `database.py` | ✅ Modified | PostgreSQL support + env-based switching |
| `alembic/env.py` | ✅ Modified | Import models, use DATABASE_URL |
| `alembic/versions/5XXX_initial.py` | ✅ Created | Initial migration |
| `.env.dev` | ✅ Created | Development environment config |
| `.env.prod` | ✅ Created | Production environment template |
| `.env.example` | ✅ Updated | Comprehensive configuration guide |

---

## 🔧 What USER Must Configure

### **Option 1: Continue with SQLite (Development)**

**No action required!** The system defaults to SQLite if `DATABASE_URL` is not set.

```bash
# Your .env (or no .env at all)
DATABASE_URL=

# System will use: sqlite:///./solvestack.db
```

---

### **Option 2: Setup PostgreSQL Locally**

#### Step 1: Install PostgreSQL

**Windows**:
```bash
# Download from: https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

**macOS**:
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Step 2: Create Database & User

```bash
# Access PostgreSQL
psql -U postgres

# In psql shell:
CREATE DATABASE solvestack;
CREATE USER solvestack_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE solvestack TO solvestack_user;
\q
```

#### Step 3: Update .env

```bash
# .env
DATABASE_URL=postgresql://solvestack_user:your_secure_password@localhost:5432/solvestack
```

#### Step 4: Run Migration

```bash
# Apply migration to PostgreSQL
alembic upgrade head

# You should see:
# INFO  [alembic.runtime.migration] Running upgrade  -> 5XXXXX, Initial migration
```

#### Step 5: Verify

```bash
# Check tables were created
psql -U solvestack_user -d solvestack

# In psql:
\dt  # List all tables
# You should see: users, problems, collaboration_groups, etc.
```

---

### **Option 3: Use Cloud PostgreSQL (Production)**

#### **Render.com (Recommended)**

1. Create PostgreSQL database on Render
2. Copy the "External Database URL"
3. Add to `.env.prod`:
   ```
   DATABASE_URL=postgresql://user:pass@dpg-xxxxx.oregon-postgres.render.com/db_name
   ```

#### **AWS RDS**

1. Create RDS PostgreSQL instance
2. Get endpoint from AWS Console
3. Format: `postgresql://username:password@endpoint:5432/database`

#### **Heroku Postgres**

```bash
heroku addons:create heroku-postgresql:mini
heroku config:get DATABASE_URL
```

---

## 🧪 How to Test

### **Test 1: Verify Database Mode**

```bash
# In d:\major proj demo
python -c "from database import engine; print(engine.url)"

# Expected output:
# SQLite: sqlite:///./solvestack.db
# PostgreSQL: postgresql://user@host:5432/solvestack
```

### **Test 2: Run Migration (PostgreSQL)**

```bash
# Upgrade to latest
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### **Test 3: Create Sample Migration**

```bash
# Make a change to models.py (add a field)
# Then generate migration
alembic revision --autogenerate -m "Add new field to Problem"

# Review generated migration in alembic/versions/
# Apply it
alembic upgrade head
```

### **Test 4: Verify Backend Still Works**

```bash
# Start uvicorn (should auto-reload)
uvicorn main:app --reload

# Open Swagger
http://localhost:8000/docs

# Test endpoints (should work with either SQLite or PostgreSQL)
```

---

## 🎓 IEEE Paper Contribution

### **Research Elements Demonstrated:**

1. **Scalable Architecture Design**
   - Dual-mode database support (dev vs prod)
   - Environment-based configuration
   - Connection pooling for concurrency

2. **Schema Version Control**
   - Alembic for migration management
   - Automatic schema detection
   - Forward and backward compatibility

3. **Production Best Practices**
   - Separation of environments (.env.dev vs .env.prod)
   - No hardcoded credentials
   - Database abstraction layer

### **Paper Sections This Supports:**

**System Architecture** (Section 3.1):
> "SolveStack employs a flexible database layer supporting both SQLite for rapid development and PostgreSQL for production deployment. Schema versioning is managed through Alembic, ensuring smooth evolution of the data model while maintaining data integrity across migrations."

**Scalability Considerations** (Section 4.2):
> "The system's database architecture supports horizontal scaling through PostgreSQL's connection pooling (pool_size=10, max_overflow=20), enabling concurrent request handling in production environments."

**Deployment Strategy** (Section 5.1):
> "Environment-based configuration allows seamless transitions between development, staging, and production environments without code changes, reducing deployment risks."

---

## 🔄 Migration Workflow

### **Day-to-Day Development**

```bash
# 1. Modify models.py
class User(Base):
    new_field = Column(String(100))  # Add this

# 2. Generate migration
alembic revision --autogenerate -m "Add new_field to User"

# 3. Review migration file
# Check alembic/versions/XXXXX_add_new_field_to_user.py

# 4. Apply migration
alembic upgrade head

# 5. Commit migration file to git
git add alembic/versions/XXXXX_add_new_field_to_user.py
git commit -m "Add new_field to User model"
```

### **Production Deployment**

```bash
# On production server
git pull
pip install -r requirements.txt
alembic upgrade head  # Apply new migrations
systemctl restart solvestack  # Restart service
```

---

## ⚠️ Important Notes

### **DO NOT**:
- ❌ Delete migration files
- ❌ Modify existing migrations after applying them
- ❌ Commit `.env` files to git (only `.env.example`)
- ❌ Use SQLite in production (no concurrent writes)

### **DO**:
- ✅ Review auto-generated migrations before applying
- ✅ Test migrations on development database first
- ✅ Keep `.env.example` up to date
- ✅ Use PostgreSQL for production deployments
- ✅ Backup database before major migrations

---

## 🚀 Next Steps

**Phase 3.1 Complete!** Database infrastructure is production-ready.

**Ready for Phase 3.2** (if needed): Further environment management improvements.

**OR proceed to Phase 4**: Multi-source scraping (GitHub Issues).

---

## 📝 Quick Reference

**Alembic Commands**:
```bash
alembic upgrade head        # Apply all migrations
alembic downgrade -1        # Rollback one migration
alembic current             # Show current version
alembic history             # Show all migrations
alembic revision -m "msg"   # Create empty migration
alembic revision --autogenerate -m "msg"  # Auto-generate from models
```

**Database URLs**:
```
SQLite:      sqlite:///./solvestack.db
Local PG:    postgresql://user:pass@localhost:5432/solvestack
Render:      postgresql://user:pass@dpg-xxx.oregon-postgres.render.com/db
AWS RDS:     postgresql://user:pass@xxx.us-east-1.rds.amazonaws.com:5432/db
```

---

**Phase 3.1 Status**: ✅ **PRODUCTION READY**

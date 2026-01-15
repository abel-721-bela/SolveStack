# SIMPLE FIX: PostgreSQL Migration Without Alembic

## 🔧 The Problem

Your system is **STILL using SQLite** even with DATABASE_URL set because:
1. `.env` file might not have the DATABASE_URL
2. Or Python isn't loading it properly

## ✅ SIMPLE SOLUTION (Skip Alembic for now)

### **Step 1: Verify .env File**

Open `d:\major proj demo\.env` and make sure it contains:

```
DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack
SECRET_KEY=dev-secret-key
```

**Important**: No quotes, no spaces around `=`

### **Step 2: Test Database Connection Directly**

```powershell
cd "d:\major proj demo"
python
```

Then in Python shell:
```python
import os
from dotenv import load_dotenv

load_dotenv()
print("DATABASE_URL:", os.getenv("DATABASE_URL"))

from database import engine
print("Engine URL:", engine.url)
```

You should see PostgreSQL URL, NOT sqlite.

### **Step 3: Create Tables Directly (Skip Alembic)**

Instead of using Alembic migrations, just create tables directly:

```powershell
python -c "from models import Base; from database import engine; print(engine.url); Base.metadata.create_all(bind=engine); print('Tables created!')"
```

This will create all tables in PostgreSQL directly.

### **Step 4: Verify Tables Created**

```powershell
# Connect to PostgreSQL
psql -U postgres -d solvestack

# In psql:
\dt  # List all tables

# You should see:
# users, problems, collaboration_groups, collaboration_requests, etc.
```

### **Step 5: Restart Backend**

```powershell
# Stop uvicorn (Ctrl+C)
# Start again:
uvicorn main:app --reload
```

---

## 🎯 If This Still Doesn't Work

**Option A: Check if .env file exists**
```powershell
dir .env
```

**Option B: Set DATABASE_URL directly in PowerShell (temporary test)**
```powershell
$env:DATABASE_URL="postgresql://postgres:1234@localhost:5432/solvestack"
python -c "from database import engine; print(engine.url)"
```

**Option C: Hardcode for testing (NOT for production)**

Edit `database.py` line 22:
```python
# Temporarily hardcode for testing
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/solvestack"
```

---

## 📋 Summary

**Don't use Alembic yet** - It's causing issues with migration compatibility.

**Just use**: `Base.metadata.create_all(bind=engine)`

This creates all tables from your models directly in PostgreSQL.

**Once working**, we can set up Alembic properly later.

Try Step 2 first to see what DATABASE_URL is being loaded!

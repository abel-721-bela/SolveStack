# URGENT FIX: Your .env File Has Wrong DATABASE_URL

## ❌ The Problem

Your `.env` file currently has:
```
DATABASE_URL=sqlite:///./problems.db
```

This is **WRONG** for PostgreSQL!

## ✅ The Fix

**Replace your `.env` file** with this content:

```
# SolveStack Environment - PostgreSQL Mode
DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack
SECRET_KEY=dev-secret-key-change-later-12345
```

## 📝 Step-by-Step

### **Option 1: Manual Fix (Fastest)**

1. Open `.env` file in VSCode
2. Find the line: `DATABASE_URL=sqlite:///./problems.db`
3. Replace with: `DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack`
4. Save the file

### **Option 2: Use Pre-Made File**

```powershell
# Backup your current .env
copy .env .env.backup

# Copy the corrected version
copy .env.CORRECTED .env
```

### **Option 3: Command Line**

```powershell
# Delete old .env
del .env

# Create new .env with correct content
echo DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack > .env
echo SECRET_KEY=dev-secret-key >> .env
```

---

## 🧪 Test It Works

After fixing .env, run:

```powershell
python test_pg_connection.py
```

You should see:
```
✅ DATABASE_URL loaded
✅ Using PostgreSQL!
✅ All tables created successfully!
```

Then restart uvicorn:
```powershell
# Stop current uvicorn (Ctrl+C)
uvicorn main:app --reload
```

---

## 🎯 Quick Summary

**Problem**: `.env` had SQLite URL instead of PostgreSQL  
**Fix**: Change `DATABASE_URL=` line to PostgreSQL connection string  
**Test**: Run `python test_pg_connection.py`  
**Result**: Tables will be created in PostgreSQL automatically!

**No Alembic needed** - just fix the .env file and run the test script!

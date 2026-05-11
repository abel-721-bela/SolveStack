# Quick Fix Guide for PostgreSQL Migration

## ✅ Steps to Fix the Migration Error

### **Step 1: Update .env File**

Add this to your `.env` file (create if it doesn't exist):

```
DATABASE_URL=postgresql://postgres:1234@localhost:5432/solvestack
SECRET_KEY=dev-secret-key-change-in-production
```

### **Step 2: Restart uvicorn**

The changes to `.env` won't be picked up until you restart uvicorn:

```powershell
# Stop uvicorn (Ctrl+C in the terminal running it)
# Then restart:
uvicorn main:app --reload
```

### **Step 3: Run Migration Again**

```powershell
alembic upgrade head
```

### **Step 4: Verify PostgreSQL Connection**

```powershell
python -c "from database import engine; print(engine.url)"
```

You should see: `postgresql://postgres@localhost:5432/solvestack`

---

## 🔧 What I Fixed

1. **Removed invalid DROP TABLE** - Migration was trying to drop `problem_states` table that doesn't exist
2. **Updated migration file** - Cleaned up auto-generated migration

---

## ⚠️ Important Notes

- **Environment variables in PowerShell** (`set VAR=value`) are temporary
- **Always use .env file** for persistent configuration
- **Restart uvicorn** after changing .env

---

## 🎯 Current Status

- ✅ Migration file fixed
- ⏳ Waiting for you to:
  1. Add DATABASE_URL to .env
  2. Restart uvicorn
  3. Run `alembic upgrade head`

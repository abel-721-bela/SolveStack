# 🚀 Setup Instructions for Teammates

Welcome to **SolveStack**! Follow these step-by-step instructions to get the project running on your machine.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.9 or higher** installed
  - Verify: `python --version`
- [ ] **PostgreSQL 15+** installed and running
  - Verify: `psql --version`
- [ ] **Git** installed
  - Verify: `git --version`
- [ ] **pip** package manager
  - Verify: `pip --version`

---

## 📥 Step 1: Clone the Repository

```bash
git clone <repository-url>
cd major-proj-demo
```

---

## 🐍 Step 2: Create Python Virtual Environment

### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### On macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

**Verify activation:** Your terminal should show `(venv)` prefix.

---

## 📦 Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output:** Installation of ~40 packages including FastAPI, SQLAlchemy, PyTorch, etc.

**⏱️ Time:** ~5-10 minutes depending on internet speed.

---

## 🗄️ Step 4: Set Up PostgreSQL Database

### Option A: Using psql command line
```bash
# Open PostgreSQL prompt
psql -U postgres

# Create database
CREATE DATABASE solvestack;

# Exit
\q
```

### Option B: Using pgAdmin
1. Open pgAdmin
2. Right-click "Databases" → Create → Database
3. Name: `solvestack`
4. Click Save

**Verify:** 
```bash
psql -U postgres -l | grep solvestack
```

---

## 🔐 Step 5: Configure Environment Variables

### 5.1 Copy Template
```bash
cp .env.example .env
```

### 5.2 Edit .env File

Open `.env` in your text editor and update the following:

#### Required Configuration

```bash
# Database Connection
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/solvestack
# Replace YOUR_PASSWORD with your PostgreSQL password

# JWT Secret (Generate a new one!)
SECRET_KEY=<run this command to generate>
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output and paste it as your `SECRET_KEY` value.

#### API Credentials (for scraping)

##### Reddit API
1. Go to: https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" type
4. Fill in name and description
5. Copy `client_id` and `client_secret`

```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=platform:YourAppName:1.0 (by /u/YourUsername)
```

##### Stack Overflow API (Optional)
1. Go to: https://stackapps.com/apps/oauth/register
2. Register your application
3. Copy the key

```bash
STACKEXCHANGE_KEY=your_key_here
```

##### GitHub Token (Highly Recommended)
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Classic"
3. Select scopes: `public_repo`, `read:org`
4. Generate and copy token

```bash
GITHUB_TOKEN=your_github_token_here
```

**Why GitHub Token?**
- Without token: 60 requests/hour
- With token: 5000 requests/hour

---

## 🗃️ Step 6: Run Database Migrations

```bash
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 5a63c0e90964, initial migration all solvestack models
INFO  [alembic.runtime.migration] Running upgrade 5a63c0e90964 -> 29f5c06cdf21, add phase 4 fields source_id humanized_
```

**Verify migrations:**
```bash
alembic current
```

---

## 🎯 Step 7: Start the Application

```bash
uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['D:\\major proj demo']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## ✅ Step 8: Verify Installation

### 8.1 Check API Documentation
Open browser and navigate to:
```
http://127.0.0.1:8000/docs
```

You should see the **FastAPI Swagger UI** with all endpoints listed.

### 8.2 Run Database Verification
```bash
# In a new terminal (keep server running)
python verify_db.py
```

**Expected output:** Summary of database tables and their structures.

### 8.3 Test Backend Connection
```bash
python test_pg_connection.py
```

**Expected output:** 
```
✅ Database connection successful
✅ All tables exist
```

---

## 🧪 Step 9: Run Tests (Optional but Recommended)

### Test Individual Scrapers
```bash
python test_individual_scrapers.py
```

### Test Unified Scraping
```bash
python test_scrape_all_endpoint.py
```

### Test Backend API
```bash
python test_backend.py
```

---

## 🎉 Step 10: Start Using the Application

### Create Your First User
Using the API docs at `http://127.0.0.1:8000/docs`:

1. Navigate to **POST /register**
2. Click "Try it out"
3. Fill in:
   ```json
   {
     "username": "yourname",
     "email": "your@email.com",
     "password": "securepassword"
   }
   ```
4. Click "Execute"

### Login and Get Token
1. Navigate to **POST /token**
2. Enter username and password
3. Copy the `access_token` from response
4. Click "Authorize" button at top
5. Paste token in format: `Bearer your_token_here`

### Scrape Your First Problems
1. Navigate to **POST /scrape/all**
2. Click "Try it out"
3. Click "Execute"
4. Wait for scraping to complete (~30-60 seconds)

### View Problems
1. Navigate to **GET /problems**
2. Click "Try it out"
3. Click "Execute"
4. You should see 30 problems from various sources!

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:** Ensure virtual environment is activated
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Issue: "Database connection failed"
**Solution:** 
1. Check PostgreSQL is running:
   ```bash
   # Windows
   pg_ctl status
   
   # Linux
   sudo service postgresql status
   ```
2. Verify DATABASE_URL in `.env`
3. Test connection:
   ```bash
   psql -U postgres -d solvestack
   ```

### Issue: "Port 8000 already in use"
**Solution:** Kill existing process or use different port:
```bash
uvicorn main:app --reload --port 8001
```

### Issue: "Rate limit exceeded" for scrapers
**Solution:** 
- Add GitHub token to `.env`
- Wait for rate limit reset
- Reduce scraping frequency

### Issue: "Alembic migration failed"
**Solution:**
```bash
# Check current migration
alembic current

# Rollback one step
alembic downgrade -1

# Re-run upgrade
alembic upgrade head
```

---

## 📁 Important Files Reference

| File | Purpose |
|------|---------|
| `.env` | Your local environment variables (DO NOT COMMIT) |
| `main.py` | FastAPI application entry point |
| `requirements.txt` | Python dependencies |
| `alembic.ini` | Database migration configuration |
| `README.md` | Project overview and documentation |

---

## 🔄 Daily Development Workflow

1. **Start Development:**
   ```bash
   cd major-proj-demo
   venv\Scripts\activate  # or source venv/bin/activate
   uvicorn main:app --reload
   ```

2. **Make Changes:**
   - Edit Python files
   - Server auto-reloads on save

3. **Test Changes:**
   ```bash
   # Run relevant test scripts
   python test_backend.py
   ```

4. **Commit Changes:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```

---

## 🆘 Need Help?

- **API Documentation:** http://127.0.0.1:8000/docs
- **Project Status:** See `docs/PROJECT_STATUS.md`
- **Testing Guide:** See `TESTING_GUIDE.md`
- **Collaboration Guide:** See `COLLABORATION_TESTING.md`

---

## 🎓 Next Steps

Once you have the project running:

1. **Explore the API** - Try different endpoints in the docs
2. **Run Scrapers** - Test each scraper individually
3. **Review Code** - Understand the project structure
4. **Add Features** - Pick a task from the backlog
5. **Write Tests** - Add test coverage for new features

---

**Happy Coding! 🚀**

If you encounter any issues not covered here, please reach out to the team or create an issue on GitHub.

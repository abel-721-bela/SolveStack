# SolveStack Backend Setup Guide

## Quick Start

### 1. Environment Setup

**Create `.env` file** (user.env for reference)
Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Copy example file
copy .env.example .env

# Edit .env with your values:
# - Reddit API credentials (already filled)
# - DATABASE_URL for PostgreSQL
# - SECRET_KEY for JWT (generate a random string)
# - Optional: GITHUB_TOKEN, STRIPE keys
```

### 2. Install Dependencies

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install all requirements
pip install -r requirements.txt
```

### 3. Database Setup

**Option A: Use SQLite (Quick Testing)**
```bash
# SQLite works automatically, no setup needed
# DATABASE_URL in .env can be: sqlite:///problems.db
```

**Option B: Use PostgreSQL (Production)**

```bash
# Install PostgreSQL first: https://www.postgresql.org/download/

# Create database
psql -U postgres
CREATE DATABASE solvestack;
\q

# Update .env
# DATABASE_URL=postgresql://postgres:your_password@localhost:5432/solvestack

# Run migration (if you have existing SQLite data)
python migrate_data.py
```

### 4. Run the Application

```bash
# Start FastAPI backend
uvicorn main:app --reload

# API will be available at:
# http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 5. Test the API

**Health Check:**
```bash
curl http://localhost:8000/
```

**Get Problems:**
```bash
curl http://localhost:8000/problems
```

**Register User:**
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"password123\"}"
```

**Login:**
```bash
curl -X POST http://localhost:8000/login \
  -F "username=test@example.com" \
  -F "password=password123"
```

---

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `GET /me` - Get current user info (requires auth)

### Problems
- `GET /problems` - List all problems (filters: tech, source)
- `GET /problems/{id}` - Get problem details
- `POST /scrape` - Trigger scraping (admin)

### Collaboration
- `POST /interest` - Mark interest in problem (requires auth)
- `DELETE /interest/{id}` - Remove interest
- `POST /collaborate/request` - Join collaboration (requires premium)

---

## Next Steps

1. **Test locally** with SQLite or PostgreSQL
2. **Update frontend** to call new FastAPI endpoints
3. **Set up Stripe** for premium subscriptions
4. **Deploy to Render** for production

---

## Troubleshooting

**ImportError: No module named 'x'**
- Run: `pip install -r requirements.txt`

**Database connection error**
- Check `.env` DATABASE_URL is correct
- Make sure PostgreSQL is running (if using it)

**JWT token errors**
- Make sure SECRET_KEY is set in `.env`

**Reddit API errors**
- Check REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in `.env`

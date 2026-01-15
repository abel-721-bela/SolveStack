# SolveStack - Real-World Problem Discovery Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Project Overview

**SolveStack** is an intelligent platform for discovering, curating, and collaborating on real-world technical problems from multiple sources including Reddit, Stack Overflow, Hacker News, and GitHub. It uses AI-powered classification to help developers, researchers, and teams find meaningful problems to solve.

### Key Features
- 🔍 **Multi-Platform Scraping**: Automated discovery from 4+ sources
- 🤖 **AI-Powered Classification**: Difficulty scoring and solution possibility analysis
- 👥 **Team Collaboration**: Real-time chat, voting, and problem discussions
- 🔐 **Secure Authentication**: JWT-based auth with role management
- 📊 **Smart Filtering**: De-duplication, quality scoring, and intelligent categorization
- 🗄️ **Production-Ready**: PostgreSQL + Alembic migrations for schema versioning

---

## 🚀 Quick Start for Teammates

### Prerequisites
- **Python 3.9+** installed
- **PostgreSQL 15+** installed and running
- **Git** installed
- API credentials for scraping sources (see Environment Setup)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd major-proj-demo
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure PostgreSQL Database
```bash
# Open PostgreSQL command line
psql -U postgres

# Create database
CREATE DATABASE solvestack;

# Exit PostgreSQL
\\q
```

### Step 4: Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# See "Environment Variables" section below
```

### Step 5: Run Database Migrations
```bash
# Initialize Alembic (if needed)
alembic upgrade head
```

### Step 6: Run the Application
```bash
# Start the FastAPI server
uvicorn main:app --reload

# Server will be available at:
# http://127.0.0.1:8000
# API docs at: http://127.0.0.1:8000/docs
```

---

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure the following:

### Required Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/solvestack

# JWT Authentication
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### API Credentials (for scraping)
```bash
# Reddit API (https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=platform:YourAppName:1.0 (by /u/YourUsername)

# Stack Overflow (https://stackapps.com/apps/oauth/register)
STACKEXCHANGE_KEY=your_stackexchange_key

# GitHub Token (https://github.com/settings/tokens)
GITHUB_TOKEN=your_github_token  # Optional but recommended
```

### Optional Variables
```bash
# Stripe (for payments)
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_PUBLISHABLE_KEY=your_publishable_key
STRIPE_PRICE_ID=your_price_id

# Firebase (for real-time chat)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
```

---

## 📁 Project Structure

```
major-proj-demo/
├── main.py                   # FastAPI application entry point
├── models.py                 # SQLAlchemy database models
├── schemas.py                # Pydantic schemas for validation
├── database.py               # Database connection & session management
├── auth.py                   # JWT authentication logic
├── scoring_engine.py         # AI-powered problem classification
│
├── scrapers/                 # Multi-platform scraping modules
│   ├── __init__.py
│   ├── reddit_scraper.py
│   ├── stackoverflow_scraper.py
│   ├── hackernews_scraper.py
│   └── github_scraper.py
│
├── alembic/                  # Database migrations
│   ├── versions/             # Migration scripts
│   ├── env.py
│   └── alembic.ini
│
├── tests/                    # Test scripts
│   ├── test_backend.py
│   ├── test_scrapers.py
│   ├── test_scrape_all_endpoint.py
│   └── ...
│
├── docs/                     # Documentation
│   ├── PROJECT_STATUS.md
│   ├── TESTING_GUIDE.md
│   └── ...
│
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
└── requirements.txt          # Python dependencies
```

---

## 🧪 Running Tests

### Test Individual Scrapers
```bash
python test_individual_scrapers.py
```

### Test Scrape All Endpoint
```bash
python test_scrape_all_endpoint.py
```

### Test Backend API
```bash
python test_backend.py
```

### Test Database Connection
```bash
python test_pg_connection.py
```

### Verify Database Schema
```bash
python verify_db.py
```

---

## 🛠️ Development Workflow

### Creating New Database Migrations
```bash
# After modifying models.py
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### Scraping Problems
```bash
# Scrape from all sources (30 problems per run)
curl -X POST http://127.0.0.1:8000/scrape/all

# Check logs for details on fetched/inserted/skipped problems
```

### Adding Sample Data
```bash
python add_sample_problems.py
```

---

## 📊 API Endpoints

### Authentication
- `POST /register` - Create new user account
- `POST /token` - Login and get JWT token

### Problems
- `GET /problems` - List all problems (with filters)
- `GET /problems/{id}` - Get specific problem
- `POST /scrape/all` - Trigger scraping from all sources

### Collaboration
- `POST /problems/{id}/vote` - Upvote/downvote problem
- `POST /problems/{id}/claim` - Claim problem for solving
- `GET /problems/{id}/collaborators` - List collaborators

### Admin
- `GET /db/info` - Database statistics

Full API documentation available at: `http://127.0.0.1:8000/docs`

---

## 📖 Additional Documentation

- **[PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** - Current development status and roadmap
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing instructions
- **[PHASE3_1_MIGRATION.md](PHASE3_1_MIGRATION.md)** - Database migration guide
- **[COLLABORATION_TESTING.md](COLLABORATION_TESTING.md)** - Team collaboration features

---

## 🤝 Contributing

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes and test thoroughly
3. Run linting: `black . && flake8`
4. Commit: `git commit -m "Add your feature"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

---

## 🐛 Troubleshooting

### "This site can't be reached" error
- Ensure uvicorn is running: `uvicorn main:app --reload`
- Check if port 8000 is available
- Verify no firewall blocking

### Database connection errors
- Verify PostgreSQL is running: `pg_ctl status`
- Check `DATABASE_URL` in `.env`
- Ensure database exists: `psql -U postgres -l`

### Import errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### Migration errors
- Check current migration: `alembic current`
- Rollback if needed: `alembic downgrade -1`
- Re-run: `alembic upgrade head`

---

## 📝 License

This project is licensed under the MIT License.

---

## 📧 Contact & Support

For questions, issues, or contributions, please contact the team or open an issue on GitHub.

**Happy Problem Solving! 🚀**

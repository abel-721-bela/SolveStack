# SolveStack - Crowdsourced Tech Problems Platform

A platform that crowdsources real-world tech problems from Reddit, GitHub, and other platforms, turning them into structured project ideas for developers to collaborate on.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (or SQLite for testing)
- Node.js 16+ (for frontend)

### Backend Setup

1. **Create environment file**
   ```bash
   # Copy the example and fill in your values
   copy .env.example .env
   ```
   
   Required values in `.env`:
   - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` (already filled)
   - `DATABASE_URL` (PostgreSQL or SQLite)
   - `SECRET_KEY` (generate a random string for JWT)

2. **Install dependencies**
   ```bash
   # Activate virtual environment
   venv\Scripts\activate
   
   # Install Python packages
   pip install -r requirements.txt
   ```

3. **Run database migration** (if you have existing SQLite data)
   ```bash
   python migrate_data.py
   ```

4. **Start the API server**
   ```bash
   uvicorn main:app --reload
   ```
   
   API will be available at: http://localhost:8000
   Interactive API docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd problem-shelf-frontend
npm install
npm start
```

Frontend will be available at: http://localhost:3000

---

## 📁 Project Structure

```
d:/major proj demo/
├── main.py                 # FastAPI application
├── models.py              # SQLAlchemy ORM models
├── database.py            # Database connection
├── schemas.py             # Pydantic schemas for validation
├── auth.py                # JWT authentication
├── pyproblem_shelf.py     # Scraping logic (Reddit + GitHub)
├── migrate_data.py        # SQLite to PostgreSQL migration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this!)
├── .env.example           # Environment template
├── BACKEND_SETUP.md       # Detailed backend guide
│
└── problem-shelf-frontend/  # React frontend
    ├── src/
    │   ├── pages/         # Dashboard, Suggest, Admin
    │   └── components/    # ProblemCard, Navbar, etc.
    └── package.json
```

---

## 🔑 Features

### Implemented ✅
- **Multi-platform scraping**: Reddit + GitHub Issues
- **AI classification**: Zero-shot NLP to filter tech-solvable problems
- **FastAPI backend**: RESTful API with automatic docs
- **User authentication**: JWT-based auth with bcrypt passwords
- **Interest tracking**: Users can mark interest in problems
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Duplicate detection**: Unique constraint on reference links
- **React frontend**: Material-UI dashboard

### In Progress 🚧
- **Collaboration rooms**: Premium users can chat and share files
- **Stripe integration**: Freemium monetization model
- **Deployment**: Render (backend) + Vercel (frontend)

---

## 🛠️ API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Health check | No |
| POST | `/register` | Register new user | No |
| POST | `/login` | Login and get JWT token | No |
| GET | `/me` | Get current user info | Yes |
| GET | `/problems` | List all problems | No |
| GET | `/problems/{id}` | Get problem details | No |
| POST | `/scrape` | Trigger scraping | No (will add admin auth) |
| POST | `/interest` | Mark interest in problem | Yes |
| DELETE | `/interest/{id}` | Remove interest | Yes |
| POST | `/collaborate/request` | Join collaboration room | Yes (Premium) |

---

## 🧪 Testing

### Test API Endpoints

**1. Register a user:**
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"password123\"}"
```

**2. Login:**
```bash
curl -X POST http://localhost:8000/login \
  -F "username=test@example.com" \
  -F "password=password123"
```

**3. Get problems:**
```bash
curl http://localhost:8000/problems
```

**Or use the interactive API docs:**
http://localhost:8000/docs

---

## 📊 Database Schema

### Users
- `id`: Primary key
- `email`: Unique email
- `username`: Unique username
- `hashed_password`: Bcrypt hash
- `is_premium`: Boolean (free vs paid)
- `created_at`: Timestamp

### Problems
- `ps_id`: Primary key
- `title`: Problem title
- `description`: Full description
- `source`: Platform (reddit/subreddit, github/repo)
- `suggested_tech`: AI-suggested tech stack
- `reference_link`: Unique source URL
- `tags`: JSON array of tags
- `scraped_at`: Timestamp

### Many-to-Many: Users ↔ Problems (interests)

---

## 🚢 Deployment

### Backend (Render)
1. Create PostgreSQL database on Render
2. Add environment variables
3. Deploy from GitHub repo
4. Run: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)
1. Import GitHub repo
2. Set build command: `npm run build`
3. Set output directory: `build`
4. Add environment variable `REACT_APP_API_URL`

---

## 📝 License

MIT License - feel free to use this project!

---

## 🤝 Contributing

This is a university project for S8 presentation. Not currently accepting external contributions.

---

## 📧 Contact

For questions about this project, contact the development team.

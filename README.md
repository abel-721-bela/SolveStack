<p align="center">
  <img src="https://img.shields.io/badge/SolveStack-Build_What_Matters-000000?style=for-the-badge&labelColor=000000&color=06b6d4" alt="SolveStack" />
</p>

<h1 align="center">SolveStack</h1>

<p align="center">
  <strong>An AI-powered platform for discovering, curating, and collaborating on real-world technical problems.</strong>
</p>

<p align="center">
  <em>Stop building to-do apps. Start solving problems people are actually asking for.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/TypeScript-5.8-3178C6?logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</p>

---

## Overview

**SolveStack** is a full-stack intelligent platform that scrapes high-signal technical problems from across the internet — Reddit, Stack Overflow, Hacker News, and GitHub Issues — and transforms them into curated, AI-classified problem cards that developers can explore, discuss, and collaborate on in real time.

The platform features a multi-stage AI pipeline that cleans raw data, scores engineering impact, generates human-readable summaries, and enables semantic search — all served through a modern React frontend with real-time WebSocket chat.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SOLVESTACK ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   React +    │    │   FastAPI    │    │    PostgreSQL        │  │
│  │  TypeScript  │◄──►│   Backend    │◄──►│    + pgvector        │  │
│  │   (Vite)     │    │  (Uvicorn)   │    │                      │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘  │
│                             │                                       │
│              ┌──────────────┼──────────────┐                       │
│              │              │              │                        │
│         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐                  │
│         │ Scraper │   │   AI    │   │ Search  │                   │
│         │ Engine  │   │Pipeline │   │ Engine  │                   │
│         └────┬────┘   └────┬────┘   └────┬────┘                  │
│              │              │              │                        │
│    ┌─────┬──┴──┬─────┐    │         ┌────┴────┐                  │
│    │     │     │     │    │         │Semantic │                   │
│    ▼     ▼     ▼     ▼    ▼         │+Keyword │                   │
│  Reddit  SO   HN  GitHub  EIS       │ Hybrid  │                  │
│                        Scoring      └─────────┘                   │
│                        Humanizer                                   │
│                        Embeddings                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Data Pipeline
| Feature | Description |
|---|---|
| **Multi-Platform Scraping** | Automated ingestion from Reddit, Stack Overflow, Hacker News, and GitHub Issues with per-source rate limiting and quota enforcement (30 problems/run) |
| **3-Layer Deduplication** | Reference link uniqueness → SHA-256 title hashing → Fuzzy title similarity (>85%) to eliminate duplicates |
| **Quality Gate** | Rejects non-English, gibberish, and low-signal content before database insertion |
| **Data Cleaning** | HTML entity stripping, code block extraction, title normalization, and deep text sanitization |

### AI & Intelligence
| Feature | Description |
|---|---|
| **Engineering Impact Scoring (EIS)** | Multi-dimensional scoring across Technical Depth, Industry Impact, Cognitive Complexity, and Signal Quality — normalized to a 0–100 composite score |
| **Humanized Explanations** | AI-generated plain-English summaries using Gemini → Groq → Heuristic fallback chain |
| **Semantic Search** | `all-MiniLM-L6-v2` sentence embeddings with cosine similarity ranking, merged with keyword/tag boosting for hybrid retrieval |
| **Intent-Aware Search** | Two-stage recall→precision architecture with synonym expansion, embedding caching, and search logging |

### Collaboration
| Feature | Description |
|---|---|
| **Squad System** | Users create named squads around problems with leader-managed join requests and member approval |
| **Real-Time Chat** | WebSocket-powered persistent chat within squads — messages stored in PostgreSQL and broadcast live |
| **Interest Tracking** | Mark/unmark interest on problems; trending problems ranked by community engagement |
| **Collaboration Requests** | Request → Accept/Reject workflow with automatic group formation when threshold is met |

### Frontend
| Feature | Description |
|---|---|
| **Dashboard (The Shelf)** | Filterable, searchable problem feed with live search-as-you-type and AI inference overlay |
| **Problem Detail** | Full problem view with EIS breakdown, humanized explanation, collaboration status, and squad info |
| **Trending** | Top 15 most-liked problems ranked by community interest |
| **Profile** | User stats, skills, interest count, and squad membership |
| **Auth** | JWT-based login/register with protected routes |

---

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 15+ with SQLAlchemy 2.0 ORM
- **Migrations:** Alembic for schema versioning
- **Auth:** JWT tokens via `python-jose` + `passlib[bcrypt]`
- **AI/ML:** Hugging Face Transformers, Sentence-Transformers (`all-MiniLM-L6-v2`), NLTK
- **LLM Integration:** Google Gemini API, Groq API (fallback)
- **Scraping:** PRAW (Reddit), PyGithub, Requests (SO/HN APIs)
- **Real-Time:** WebSocket (native FastAPI)

### Frontend
- **Framework:** React 19 + TypeScript 5.8
- **Build Tool:** Vite 6
- **Routing:** React Router v7
- **Charts:** Recharts
- **Icons:** Lucide React
- **AI Features:** Google GenAI SDK (client-side inference overlay)

---

## Project Structure

```
SolveStack/
│
├── SolveStack-main/                 # Backend (FastAPI)
│   ├── main.py                      # Application entry point — all API routes
│   ├── models.py                    # SQLAlchemy models (User, Problem, Squad, etc.)
│   ├── schemas.py                   # Pydantic request/response schemas
│   ├── database.py                  # DB engine & session management
│   ├── auth.py                      # JWT authentication helpers
│   │
│   ├── scrapers/                    # Multi-platform scraping modules
│   │   ├── reddit_scraper.py        # Reddit via PRAW
│   │   ├── stackoverflow_scraper.py # Stack Overflow API
│   │   ├── hackernews_scraper.py    # Hacker News API
│   │   └── github_scraper.py        # GitHub Issues via PyGithub
│   │
│   ├── cleaning_layer.py            # Data cleaning, normalization, quality gate
│   ├── engineering_scoring_engine.py # EIS multi-dimensional scoring
│   ├── embedding_service.py         # Sentence-Transformer embedding generation
│   ├── search_service.py            # Hybrid + intent-aware search
│   ├── reranking_service.py         # Search result re-ranking
│   ├── humanize_service.py          # AI explanation generation (Gemini/Groq)
│   ├── impact_explanation_service.py # Natural language EIS explanations
│   ├── prototype_service.py         # AI implementation plan generation
│   ├── text_utils.py                # Text processing utilities
│   │
│   ├── alembic/                     # Database migration scripts
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Environment variables (not tracked)
│
├── solvestack-frontend/             # Frontend (React + TypeScript)
│   ├── App.tsx                      # Root component with routing
│   ├── index.html                   # HTML entry point
│   ├── pages/
│   │   ├── Welcome.tsx              # Splash/welcome screen
│   │   ├── Landing.tsx              # Marketing landing page
│   │   ├── Dashboard.tsx            # Main problem shelf with search
│   │   ├── ProblemDetail.tsx         # Individual problem view
│   │   ├── Trending.tsx             # Top liked problems
│   │   ├── Interests.tsx            # User's bookmarked problems
│   │   ├── Squads.tsx               # Squad browsing & creation
│   │   ├── SquadChat.tsx            # Real-time squad chat
│   │   ├── Profile.tsx              # User profile & stats
│   │   └── Auth.tsx                 # Login/Register
│   ├── components/
│   │   ├── ProblemCard.tsx           # Reusable problem card component
│   │   └── InferenceOverlay.tsx      # AI inference sidebar
│   ├── services/
│   │   └── api.ts                   # Backend API client
│   ├── contexts/
│   │   └── AuthContext.tsx           # Authentication state management
│   ├── types.ts                     # TypeScript type definitions
│   ├── constants.tsx                # App-wide constants
│   ├── vite.config.ts               # Vite configuration
│   └── package.json                 # Node dependencies
│
├── problems.csv                     # Seed data export
└── .gitignore                       # Git ignore rules
```

---

## Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** and **npm**
- **PostgreSQL 15+** installed and running
- API keys for scraping (see Environment Setup)

### 1. Clone the Repository

```bash
git clone https://github.com/abel-721-bela/SolveStack.git
cd SolveStack
```

### 2. Backend Setup

```bash
cd SolveStack-main

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials (see below)

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn main:app --reload
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 3. Frontend Setup

```bash
cd solvestack-frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
# Frontend available at http://localhost:5173
```

---

## Environment Variables

### Backend (`SolveStack-main/.env`)

```bash
# Database (Required)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/solvestack

# JWT Authentication (Required)
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# AI Services (Required for humanized explanations)
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Reddit API (Required for Reddit scraping)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=platform:YourApp:1.0 (by /u/YourUsername)

# GitHub Token (Optional, increases rate limit to 5000 req/hr)
GITHUB_TOKEN=your_github_personal_access_token
```

### Frontend (`solvestack-frontend/.env`)

```bash
GEMINI_API_KEY=your_gemini_api_key
```

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Create a new user account |
| `POST` | `/login` | Login and receive JWT token |
| `GET` | `/me` | Get current user profile |

### Problems
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/problems` | List problems with pagination & filters |
| `GET` | `/problems/{id}` | Get problem details with collaborators |
| `GET` | `/problems/trending` | Top 15 most-liked problems |
| `GET` | `/problems/{id}/prototype` | AI-generated implementation plan |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/search` | Intent-aware search (primary) |
| `GET` | `/search/semantic` | Pure semantic vector search |
| `GET` | `/search/keyword` | Keyword-based search fallback |
| `GET` | `/search/hybrid` | Combined semantic + keyword + tag search |

### Shelf Intelligence
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/shelf` | Curated problem shelf (explore, production, architecture, high-cognitive) |
| `GET` | `/shelf/{id}/explain` | Natural language EIS explanation |
| `GET` | `/analytics/shelf` | Global shelf analytics & EIS distribution |

### Collaboration
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/interest` | Mark interest in a problem |
| `DELETE` | `/interest/{id}` | Remove interest |
| `GET` | `/me/interests` | List user's interested problems |
| `POST` | `/collaborate/request` | Request collaboration |
| `POST` | `/collaborate/accept` | Accept collaboration request |
| `GET` | `/collaborate/{id}` | Get collaboration status |

### Squads
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/squads` | List all active squads |
| `POST` | `/squads` | Create a new squad |
| `GET` | `/squads/{id}` | Get squad details |
| `POST` | `/squads/{id}/join` | Request to join a squad |
| `POST` | `/squads/{id}/accept/{uid}` | Leader accepts a member |
| `GET` | `/squads/{id}/messages` | Get squad chat history |
| `DELETE` | `/squads/{id}` | Delete squad (leader only) |
| `WS` | `/ws/squad/{id}?token=` | Real-time squad chat WebSocket |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scrape` | Scrape from selected platforms |
| `POST` | `/scrape/all` | Unified multi-source scrape (30 problems/run) |
| `POST` | `/admin/regenerate-explanations` | Batch regenerate AI explanations |
| `GET` | `/db-info` | Database connection info |

Full interactive API documentation is available at `http://localhost:8000/docs` when the server is running.

---

## Database Schema

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string username UK
        string hashed_password
        datetime created_at
        boolean is_premium
        json skills
        json interests
        int activity_score
    }
    PROBLEMS {
        int ps_id PK
        text title
        text description
        string source
        string reference_link UK
        json tags
        float engineering_impact_score
        float technical_depth_score
        float industry_impact_score
        float cognitive_complexity_score
        float signal_quality_score
        text humanized_explanation
        json embedding
        datetime scraped_at
    }
    COLLABORATION_GROUPS {
        int id PK
        int problem_id FK
        int leader_id FK
        string name
        text description
        boolean is_active
    }
    SQUAD_MESSAGES {
        int id PK
        int squad_id FK
        int sender_id FK
        text content
        datetime sent_at
    }
    SQUAD_JOIN_REQUESTS {
        int id PK
        int squad_id FK
        int user_id FK
        string status
    }
    SEARCH_LOGS {
        int id PK
        text query
        datetime timestamp
        int results_returned
        float latency_ms
    }

    USERS ||--o{ PROBLEMS : "interested_in"
    PROBLEMS ||--o{ COLLABORATION_GROUPS : "has_squads"
    USERS ||--o{ COLLABORATION_GROUPS : "leads"
    USERS }o--o{ COLLABORATION_GROUPS : "member_of"
    COLLABORATION_GROUPS ||--o{ SQUAD_MESSAGES : "has_messages"
    USERS ||--o{ SQUAD_MESSAGES : "sends"
    COLLABORATION_GROUPS ||--o{ SQUAD_JOIN_REQUESTS : "has_requests"
    USERS ||--o{ SQUAD_JOIN_REQUESTS : "requests_join"
```

---

## Scraping Pipeline

The unified `/scrape/all` endpoint orchestrates a multi-phase scraping pipeline:

1. **Phase 1 — Initial Fetch:** 10 problems from each source (GitHub, Stack Overflow, Hacker News)
2. **Phase 2 — Quota Redistribution:** If any source underdelivers, redistributes quota to others
3. **Per-Problem Processing:**
   - Raw data → **Cleaning Layer** (HTML stripping, normalization, code extraction)
   - **Quality Gate** (reject gibberish, non-technical, non-English)
   - **3-Layer Deduplication** (link → hash → fuzzy title)
   - **Embedding Generation** (384-dim sentence vectors)
   - **EIS Scoring** (multi-dimensional impact analysis)
4. **Target:** 30 high-quality, unique problems per run

---

## Search Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│  Query Processor │ ─── Normalization, Synonym Expansion
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌────────┐
│Vector │ │Keyword │ ─── Stage 1: Broad Recall
│Search │ │Search  │
└───┬───┘ └───┬────┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│   Re-Ranker     │ ─── Stage 2: Intent-Based Precision
│  (Tag Boost +   │     Title match, tech tag match,
│   Title Match)  │     description locality scoring
└────────┬────────┘
         ▼
    Ranked Results
```

---

## License

This project is licensed under the MIT License.

---

<p align="center">
  <strong>Built with purpose. Solve what matters.</strong>
</p>

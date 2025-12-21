"""
Quick script to add sample problems for testing the SolveStack frontend
"""
from database import SessionLocal
from models import Problem
from datetime import datetime

def add_sample_problems():
    db = SessionLocal()
    
    sample_problems = [
        {
            "title": "React state not updating after API call",
            "description": "I'm fetching data from an API in useEffect, updating state with the response, but the component doesn't re-render. The state remains empty even though console.log shows the data is coming through correctly. I've tried using different dependency arrays but nothing works.",
            "source": "reddit/r/reactjs",
            "suggested_tech": "React, JavaScript, useState, useEffect",
            "reference_link": "https://reddit.com/r/reactjs/sample1",
            "tags": ["react", "hooks", "state-management"],
            "author_name": "dev_user123",
            "author_id": "u_dev123",
            "date": "2024-12-20"
        },
        {
            "title": "FastAPI CORS error when calling from localhost:3000",
            "description": "My FastAPI backend is running on localhost:8000 but when I try to fetch from my React app on localhost:3000, I get CORS policy errors. I've added CORSMiddleware with allow_origins=['*'] but still getting blocked. What am I missing?",
            "source": "reddit/r/FastAPI",
            "suggested_tech": "FastAPI, Python, CORS, React",
            "reference_link": "https://reddit.com/r/FastAPI/sample2",
            "tags": ["fastapi", "cors", "backend"],
            "author_name": "backend_dev",
            "author_id": "u_backend_dev",
            "date": "2024-12-19"
        },
        {
            "title": "PostgreSQL connection pool exhausted in production",
            "description": "Our production database keeps running out of connections. We're using SQLAlchemy with default settings. After about 100 concurrent users, new requests start failing with 'connection pool exhausted' errors. How do I properly configure connection pooling?",
            "source": "github/sqlalchemy/sqlalchemy",
            "suggested_tech": "PostgreSQL, SQLAlchemy, Python, Database",
            "reference_link": "https://github.com/sqlalchemy/sqlalchemy/issues/sample1",
            "tags": ["postgresql", "sqlalchemy", "production"],
            "author_name": "ops_engineer",
            "author_id": "gh_ops_eng",
            "date": "2024-12-18"
        },
        {
            "title": "JWT authentication best practices for SPA",
            "description": "Building a Single Page Application with JWT auth. Should I store tokens in localStorage, cookies, or memory? What's the best way to handle token refresh without interrupting the user experience? Looking for production-ready patterns.",
            "source": "reddit/r/webdev",
            "suggested_tech": "JWT, Authentication, JavaScript, Security",
            "reference_link": "https://reddit.com/r/webdev/sample3",
            "tags": ["jwt", "authentication", "security"],
            "author_name": "security_dev",
            "author_id": "u_sec_dev",
            "date": "2024-12-17"
        },
        {
            "title": "Material-UI grid layout breaks on mobile",
            "description": "My responsive grid using Material-UI looks perfect on desktop but completely breaks on mobile devices. Cards are overlapping and some content is cut off. Using Grid with xs/sm/md breakpoints but something isn't working right.",
            "source": "reddit/r/reactjs",
            "suggested_tech": "Material-UI, React, CSS, Responsive Design",
            "reference_link": "https://reddit.com/r/reactjs/sample4",
            "tags": ["material-ui", "responsive", "css"],
            "author_name": "ui_developer",
            "author_id": "u_ui_dev",
            "date": "2024-12-16"
        },
        {
            "title": "Docker compose networking between frontend and backend",
            "description": "Running React frontend and FastAPI backend in separate Docker containers. Frontend can't reach backend even though they're in the same docker-compose network. Getting connection refused errors. How do I properly configure container networking?",
            "source": "github/docker/compose",
            "suggested_tech": "Docker, Docker Compose, Networking, DevOps",
            "reference_link": "https://github.com/docker/compose/issues/sample2",
            "tags": ["docker", "networking", "devops"],
            "author_name": "devops_user",
            "author_id": "gh_devops",
            "date": "2024-12-15"
        },
        {
            "title": "Firebase Realtime Database security rules",
            "description": "Need help writing security rules for Firebase Realtime Database. Want authenticated users to read/write their own data but not access other users' data. Current rules are too permissive and failing security review.",
            "source": "reddit/r/Firebase",
            "suggested_tech": "Firebase, Security, Database, Authentication",
            "reference_link": "https://reddit.com/r/Firebase/sample5",
            "tags": ["firebase", "security", "database-rules"],
            "author_name": "mobile_dev",
            "author_id": "u_mobile",
            "date": "2024-12-14"
        },
        {
            "title": "Axios interceptor not attaching JWT token",
            "description": "Set up an Axios request interceptor to automatically attach JWT tokens to all API calls. Token is in localStorage and console.log shows it's there, but the Authorization header is not being added to requests. Interceptor seems to not be firing.",
            "source": "github/axios/axios",
            "suggested_tech": "Axios, JavaScript, HTTP, Authentication",
            "reference_link": "https://github.com/axios/axios/issues/sample3",
            "tags": ["axios", "http", "authentication"],
            "author_name": "frontend_dev",
            "author_id": "gh_frontend",
            "date": "2024-12-13"
        }
    ]
    
    try:
        for problem_data in sample_problems:
            problem = Problem(**problem_data)
            db.add(problem)
        
        db.commit()
        print(f"✅ Successfully added {len(sample_problems)} sample problems to the database!")
        
        # Verify
        count = db.query(Problem).count()
        print(f"📊 Total problems in database: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding problems: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_problems()

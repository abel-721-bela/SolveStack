"""
Comprehensive Migration Script: SQLite to PostgreSQL
Migrates users, problems, and all relationship tables.
"""

import sqlite3
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Base, User, Problem, CollaborationRequest, CollaborationGroup, problem_interests, group_members
from database import engine, SessionLocal
from dotenv import load_dotenv

load_dotenv()

def get_sqlite_connection():
    return sqlite3.connect('solvestack.db')

def migrate():
    print("=" * 60)
    print("SOLVESTACK COMPREHENSIVE MIGRATION")
    print("=" * 60)
    
    # Ensure tables exist in PG
    print("\n1. Ensuring PostgreSQL schema is ready...")
    Base.metadata.create_all(bind=engine)
    print("   [OK] PG Schema verified")
    
    sqlite_conn = get_sqlite_connection()
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    pg_db: Session = SessionLocal()
    
    try:
        # 2. Migrate Users
        print("\n2. Migrating Users...")
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for u in users:
            user_data = dict(u)
            # Check if user exists
            existing = pg_db.query(User).filter(User.email == user_data['email']).first()
            if not existing:
                new_user = User(
                    id=user_data['id'],
                    email=user_data['email'],
                    username=user_data['username'],
                    hashed_password=user_data['hashed_password'],
                    created_at=datetime.fromisoformat(user_data['created_at']) if isinstance(user_data['created_at'], str) else datetime.utcnow(),
                    is_premium=bool(user_data.get('is_premium', 0)),
                    stripe_customer_id=user_data.get('stripe_customer_id')
                )
                pg_db.add(new_user)
        pg_db.commit()
        print(f"   [OK] {len(users)} users processed")

        # 3. Migrate Problems
        print("\n3. Migrating Problems...")
        cursor.execute("SELECT * FROM problems")
        problems = cursor.fetchall()
        for p in problems:
            p_data = dict(p)
            existing = pg_db.query(Problem).filter(Problem.reference_link == p_data['reference_link']).first()
            if not existing:
                # Handle JSON tags
                tags = p_data.get('tags', '[]')
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                
                raw_tags = p_data.get('raw_tags', '[]')
                if isinstance(raw_tags, str):
                    try:
                        raw_tags = json.loads(raw_tags)
                    except:
                        raw_tags = []

                new_problem = Problem(
                    ps_id=p_data['ps_id'],
                    title=p_data['title'],
                    description=p_data.get('description'),
                    source=p_data.get('source'),
                    source_id=p_data.get('source_id'),
                    date=datetime.strptime(p_data['date'], '%Y-%m-%d').date() if p_data.get('date') else None,
                    suggested_tech=p_data.get('suggested_tech'),
                    author_name=p_data.get('author_name'),
                    author_id=p_data.get('author_id'),
                    reference_link=p_data['reference_link'],
                    tags=tags,
                    raw_title=p_data.get('raw_title'),
                    raw_description=p_data.get('raw_description'),
                    raw_tags=raw_tags,
                    cleaned_title=p_data.get('cleaned_title'),
                    cleaned_description=p_data.get('cleaned_description'),
                    normalized_title=p_data.get('normalized_title'),
                    title_hash=p_data.get('title_hash'),
                    difficulty_score=p_data.get('difficulty_score', 0.0),
                    difficulty_level=p_data.get('difficulty_level', 0),
                    upvotes=p_data.get('upvotes', 0),
                    downvotes=p_data.get('downvotes', 0),
                    comment_count=p_data.get('comment_count', 0),
                    engagement_score=p_data.get('engagement_score', 0.0),
                    text_length=p_data.get('text_length', 0),
                    word_count=p_data.get('word_count', 0),
                    has_code_block=bool(p_data.get('has_code_block', 0)),
                    num_code_blocks=p_data.get('num_code_blocks', 0),
                    scraped_at=datetime.fromisoformat(p_data['scraped_at']) if p_data.get('scraped_at') else datetime.utcnow(),
                    cleaned_at=datetime.fromisoformat(p_data['cleaned_at']) if p_data.get('cleaned_at') else datetime.utcnow(),
                    clean_version=p_data.get('clean_version', '1.0.0')
                )
                
                # Handle embedding if present
                if 'embedding' in p_data and p_data['embedding']:
                    try:
                        new_problem.embedding = json.loads(p_data['embedding'])
                    except:
                        pass
                
                pg_db.add(new_problem)
        pg_db.commit()
        print(f"   [OK] {len(problems)} problems processed")

        # 4. Migrate problem_interests (Association)
        print("\n4. Migrating Problem Interests...")
        cursor.execute("SELECT * FROM problem_interests")
        interests = cursor.fetchall()
        for i in interests:
            i_data = dict(i)
            # Insert using raw SQL for association table
            stmt = text("INSERT INTO problem_interests (user_id, problem_id, created_at) VALUES (:u, :p, :c) ON CONFLICT DO NOTHING")
            pg_db.execute(stmt, {"u": i_data['user_id'], "p": i_data['problem_id'], "c": i_data['created_at']})
        pg_db.commit()
        print(f"   [OK] {len(interests)} interests processed")

        # 5. Migrate Collaboration Requests
        print("\n5. Migrating Collaboration Requests...")
        cursor.execute("SELECT * FROM collaboration_requests")
        reqs = cursor.fetchall()
        for r in reqs:
            r_data = dict(r)
            existing = pg_db.query(CollaborationRequest).filter(
                CollaborationRequest.user_id == r_data['user_id'],
                CollaborationRequest.problem_id == r_data['problem_id']
            ).first()
            if not existing:
                new_req = CollaborationRequest(
                    id=r_data['id'],
                    user_id=r_data['user_id'],
                    problem_id=r_data['problem_id'],
                    status=r_data['status'],
                    created_at=datetime.fromisoformat(r_data['created_at']) if isinstance(r_data['created_at'], str) else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(r_data['updated_at']) if isinstance(r_data['updated_at'], str) else datetime.utcnow()
                )
                pg_db.add(new_req)
        pg_db.commit()
        print(f"   [OK] {len(reqs)} requests processed")

        # 6. Migrate Collaboration Groups
        print("\n6. Migrating Collaboration Groups...")
        cursor.execute("SELECT * FROM collaboration_groups")
        groups = cursor.fetchall()
        for g in groups:
            g_data = dict(g)
            existing = pg_db.query(CollaborationGroup).filter(CollaborationGroup.problem_id == g_data['problem_id']).first()
            if not existing:
                new_group = CollaborationGroup(
                    id=g_data['id'],
                    problem_id=g_data['problem_id'],
                    created_at=datetime.fromisoformat(g_data['created_at']) if isinstance(g_data['created_at'], str) else datetime.utcnow(),
                    is_active=bool(g_data.get('is_active', 1)),
                    firebase_room_id=g_data.get('firebase_room_id')
                )
                pg_db.add(new_group)
        pg_db.commit()
        print(f"   [OK] {len(groups)} groups processed")

        # 7. Migrate group_members (Association)
        print("\n7. Migrating Group Members...")
        cursor.execute("SELECT * FROM group_members")
        members = cursor.fetchall()
        for m in members:
            m_data = dict(m)
            stmt = text("INSERT INTO group_members (group_id, user_id, joined_at) VALUES (:g, :u, :j) ON CONFLICT DO NOTHING")
            pg_db.execute(stmt, {"g": m_data['group_id'], "u": m_data['user_id'], "j": m_data['joined_at']})
        pg_db.commit()
        print(f"   [OK] {len(members)} group members processed")

        print("\n" + "=" * 60)
        print("MIGRATION SUCCESSFUL!")
        print("=" * 60)

    except Exception as e:
        pg_db.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pg_db.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate()

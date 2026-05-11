import sys
import os
import subprocess
import argparse
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from database import SessionLocal, engine
from models import Base, Problem
from scrapers import scrape_github, scrape_stackoverflow, scrape_hackernews
from scrapers.reddit_scraper import scrape_reddit
from sqlalchemy.exc import IntegrityError
from engineering_scoring_engine import get_scoring_engine
from embedding_service import get_embedding_service

# Create tables if not exist
Base.metadata.create_all(bind=engine)

from cleaning_layer import DataCleaner

def store_problems(problems, db):
    count = 0
    cleaner = DataCleaner()
    scoring_engine = get_scoring_engine()
    embedding_service = get_embedding_service()
    
    for p in problems:
        try:
            # Check if exists by link
            existing = db.query(Problem).filter(Problem.reference_link == p['reference_link']).first()
            if existing:
                continue
                
            # 1. Prepare raw data dict for cleaner
            raw_data = {
                "raw_title": p.get('title', p.get('raw_title', '')),
                "raw_description": p.get('description', p.get('raw_description', '')),
                "raw_tags": p.get('tags', p.get('raw_tags', [])),
                "source": p['source'],
                "date": p['date'],
                "author_name": p['author_name'],
                "author_id": p['author_id'],
                "reference_link": p['reference_link'],
                "source_id": p.get('source_id')
            }
            
            # 2. Apply Cleaner
            cleaned_p = cleaner.clean_problem(raw_data)
            
            # Check for duplicate by Title Hash (Deduplication)
            existing_hash = db.query(Problem).filter(Problem.title_hash == cleaned_p['title_hash']).first()
            if existing_hash:
                continue
            
            # 3. Create Model instance
            new_prob = Problem(**cleaned_p)
            
            # 4. Apply Engineering Impact Scoring
            try:
                scores = scoring_engine.calculate_scores(new_prob)
                for attr, val in scores.items():
                    setattr(new_prob, attr, val)
            except Exception as e:
                print(f"Scoring error: {e}")
            
            # 5. Apply Embedding
            try:
                emb = embedding_service.generate_embedding(
                    title=new_prob.title,
                    description=new_prob.description,
                    tags=new_prob.tags
                )
                if emb:
                    new_prob.embedding = emb
            except Exception as e:
                print(f"Embedding error: {e}")
                
            db.add(new_prob)
            db.commit()
            count += 1
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
    return count

def run():
    db = SessionLocal()
    total_added = 0
    
    print("Starting Batch Scraping...")
    
    # Target ~100 problems total. ~25-30 per source.
    limit_per_source = 30
    
    print(f"\n[1] Scraping Reddit (Limit: {limit_per_source})...")
    try:
        data = scrape_reddit(limit=limit_per_source)
        added = store_problems(data, db)
        print(f"   -> Added {added} Reddit problems")
        total_added += added
    except Exception as e:
        print(f"   -> Failed: {e}")

    print(f"\n[2] Scraping GitHub (Limit: {limit_per_source})...")
    try:
        data = scrape_github(limit=limit_per_source)
        added = store_problems(data, db)
        print(f"   -> Added {added} GitHub problems")
        total_added += added
    except Exception as e:
        print(f"   -> Failed: {e}")

    print(f"\n[3] Scraping StackOverflow (Limit: {limit_per_source})...")
    try:
        data = scrape_stackoverflow(limit=limit_per_source)
        added = store_problems(data, db)
        print(f"   -> Added {added} StackOverflow problems")
        total_added += added
    except Exception as e:
        print(f"   -> Failed: {e}")
        
    print(f"\n[4] Scraping HackerNews (Limit: {limit_per_source})...")
    try:
        data = scrape_hackernews(limit=limit_per_source)
        added = store_problems(data, db)
        print(f"   -> Added {added} HackerNews problems")
        total_added += added
    except Exception as e:
        print(f"   -> Failed: {e}")

    print(f"\nFinished! Total new problems added: {total_added}")
    db.close()

if __name__ == "__main__":
    run()

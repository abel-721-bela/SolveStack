from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Problem
from cleaning_layer import DataCleaner
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_difficulties():
    db = SessionLocal()
    cleaner = DataCleaner()
    
    problems = db.query(Problem).all()
    count = 0
    updated = 0
    
    logger.info(f"Checking {len(problems)} problems for difficulty updates...")
    
    for problem in problems:
        title = problem.cleaned_title or problem.title or ""
        desc = problem.cleaned_description or problem.description or ""
        tags = problem.tags or []
        
        new_diff = cleaner._calculate_difficulty_level(title, desc, tags)
        
        if problem.difficulty_level != new_diff:
            problem.difficulty_level = new_diff
            updated += 1
            
        count += 1
        if count % 100 == 0:
            db.commit()
            
    db.commit()
    logger.info(f"Done! Updated difficulty levels for {updated} problems.")
    db.close()

if __name__ == "__main__":
    update_difficulties()

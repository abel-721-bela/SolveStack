from main import scrape_all_sources
from database import SessionLocal
import traceback

db = SessionLocal()
try:
    print("Starting scrape...")
    res = scrape_all_sources(db=db)
    print("Scrape successful!")
    print(f"Added {res.get('total_added')} problems")
except Exception:
    traceback.print_exc()
finally:
    db.close()

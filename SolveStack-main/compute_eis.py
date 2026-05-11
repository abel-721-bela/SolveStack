import logging
from database import SessionLocal
from engineering_scoring_engine import get_scoring_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_batch_scoring():
    logger.info("Starting batch Engineering Impact Scoring (EIS)...")
    db = SessionLocal()
    try:
        engine = get_scoring_engine()
        count = engine.process_all_problems(db)
        logger.info(f"Successfully scored {count} problems.")
    except Exception as e:
        logger.error(f"Batch scoring failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_batch_scoring()

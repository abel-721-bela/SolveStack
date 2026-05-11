import logging
import argparse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Problem
from embedding_service import get_embedding_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_embeddings(batch_size=50):
    """
    Generate embeddings for problems that don't have them yet.
    """
    db: Session = SessionLocal()
    service = get_embedding_service()
    
    try:
        # 1. Process ALL problems to ensure consistency
        problems_to_process = db.query(Problem).all()
        total_to_process = len(problems_to_process)
        
        logger.info(f"Starting RE-GENERATION for {total_to_process} problems (Batch size: {batch_size})")
        
        processed_count = 0
        
        # 2. Process in batches
        for i in range(0, total_to_process, batch_size):
            batch = problems_to_process[i:i + batch_size]
            
            # Prepare texts for the batch using standardized format
            batch_texts = []
            for p in batch:
                title = p.title or ""
                description = p.description or ""
                tags = p.tags or []
                tags_str = ", ".join(tags)
                text = f"Title: {title.strip()}. Description: {description.strip()}. Tags: {tags_str}"
                
                # Truncate to 500 as per requirement
                if len(text) > 500:
                    text = text[:500]
                batch_texts.append(text)
            
            # Generate normalized embeddings for the entire batch
            batch_embeddings = service.generate_batch_embeddings(batch_texts)
            
            # Update problems
            for problem, embedding_list in zip(batch, batch_embeddings):
                problem.embedding = embedding_list
            
            # Commit the batch
            db.commit()
            processed_count += len(batch)
            logger.info(f"Progress: {processed_count}/{total_to_process} ({(processed_count/total_to_process)*100:.1f}%)")
            
        logger.info("Embedding generation complete!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during embedding generation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for SolveStack problems")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of problems to process per batch")
    args = parser.parse_args()
    
    generate_embeddings(batch_size=args.batch_size)

import logging
from database import SessionLocal
from models import Problem
from impact_explanation_service import get_explanation_service
from sqlalchemy import func, cast, JSON

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def verify_db_stats():
    db = SessionLocal()
    try:
        total = db.query(Problem).count()
        avg_eis = db.query(func.avg(Problem.engineering_impact_score)).scalar()
        logger.info(f"Total problems: {total}")
        logger.info(f"Average EIS: {avg_eis:.2f}")
        
        # Check Top Impact
        top = db.query(Problem).order_by(Problem.engineering_impact_score.desc()).limit(3).all()
        logger.info("\nTop 3 Engineering Impact Problems:")
        for p in top:
            logger.info(f"[{p.ps_id}] {p.title}")
            logger.info(f"  EIS: {p.engineering_impact_score} (D: {p.technical_depth_score}, I: {p.industry_impact_score}, C: {p.cognitive_complexity_score}, S: {p.signal_quality_score})")

        # Check Mode: Production
        prod = db.query(Problem).filter(Problem.industry_impact_score > 0.6, Problem.signal_quality_score > 0.6).limit(2).all()
        logger.info("\nMode: Production (Top 2):")
        for p in prod:
            logger.info(f"[{p.ps_id}] {p.title}")

        # Check Explainability
        if top:
            explainer = get_explanation_service()
            explanation = explainer.explain_score(top[0])
            logger.info("\nExplanation for Top Problem:")
            logger.info(f"  Thinking Type: {explanation['thinking_type']}")
            logger.info(f"  Explanation: {explanation['explanation']}")
            logger.info(f"  Signals: {', '.join(explanation['signals_contributed'])}")

    finally:
        db.close()

if __name__ == "__main__":
    verify_db_stats()

import re
import logging
from sqlalchemy.orm import Session
from models import Problem

logger = logging.getLogger(__name__)

class EngineeringImpactScoringEngine:
    VERSION = "1.0.0"
    
    # 1. Technical Depth Keywords
    DEPTH_KEYWORDS = [
        "distributed", "concurrency", "scaling", "optimization", "orchestration",
        "cicd", "ci/cd", "kubernetes", "k8s", "docker", "microservices",
        "architecture", "performance", "throughput", "latency", "bottleneck",
        "refactor", "system design", "scalability", "caching", "db", "database",
        "indexing", "concurrency", "parallelism", "asynchronous", "async",
        "react", "hooks", "state management", "redux", "vue", "nextjs", "ssr",
        "hydration", "virtual dom", "reconciliation", "memory leak", "race condition"
    ]
    
    # 2. Industry Impact Keywords
    IMPACT_KEYWORDS = [
        "production", "business", "downtime", "failure", "outage", "security",
        "vulnerability", "risk", "customer", "user", "revenue", "cost",
        "deployment", "cloud", "aws", "gcp", "azure", "infrastructure",
        "terraform", "ansible", "monitoring", "alerting", "incident", "sla", "slo",
        "authentication", "authorization", "jwt", "tls", "cors", "compliance"
    ]
    
    # 3. Cognitive Complexity Markers
    COMPLEXITY_PHRASES = [
        "trade-off", "tradeoff", "pros and cons", "pros/cons", "is it safe",
        "should we", "comparison", "alternative", "design choice", "approach",
        "best practice", "strategy", "pattern", "decision", "evaluation",
        "consistency", "availability", "partition tolerance", "idempotency"
    ]
    
    # 4. Signal Quality Penalties (Emotional Tone without Technical Density)
    EMOTIONAL_WORDS = ["frustrated", "hate", "terrible", "bad", "worst", "annoying", "ugh", "help", "please"]

    def calculate_scores(self, problem: Problem) -> dict:
        """
        Calculate deterministic scores for a problem based on content and metadata.
        """
        title = (problem.title or "").lower()
        description = (problem.description or "").lower()
        content = f"{title} {description}"
        tags = problem.tags if isinstance(problem.tags, list) else []
        
        # --- 1. Technical Depth (0.0 - 1.0) ---
        depth_hits = sum(1 for kw in self.DEPTH_KEYWORDS if kw in content)
        # Normalize: 5 keywords = 0.8, more caps at 1.0
        depth_score = min(1.0, depth_hits / 5.0)
        # Multi-domain bonus (>= 2 tags)
        if len(tags) >= 2:
            depth_score = min(1.0, depth_score + 0.2)
        
        # --- 2. Industry Impact (0.0 - 1.0) ---
        impact_hits = sum(1 for kw in self.IMPACT_KEYWORDS if kw in content)
        # Normalize: 4 keywords = 0.8
        impact_score = min(1.0, impact_hits / 4.0)
        
        # --- 3. Cognitive Complexity (0.0 - 1.0) ---
        complexity_hits = sum(1 for ph in self.COMPLEXITY_PHRASES if ph in content)
        # Ambiguity markers (question marks)
        question_count = content.count("?")
        complexity_score = min(1.0, (complexity_hits / 3.0) + (min(2, question_count) * 0.1))
        
        # --- 4. Signal Quality (0.0 - 1.0) ---
        # Length penalty
        total_len = len(content)
        len_score = min(1.0, total_len / 500.0) # 500 chars is good signal
        # Emotional penalty vs Technical ratio
        emotional_hits = sum(1 for ew in self.EMOTIONAL_WORDS if ew in content)
        technical_hits = depth_hits + impact_hits
        
        signal_quality = len_score
        if emotional_hits > 0:
            # If emotional > technical, penalize heavily
            if emotional_hits > technical_hits:
                signal_quality = max(0.0, signal_quality - 0.4)
            else:
                signal_quality = max(0.0, signal_quality - 0.1)
        
        # Reward specific tool mentions (from keywords)
        if technical_hits > 0:
            signal_quality = min(1.0, signal_quality + 0.2)
            
        # --- 5. Hard Penalties (The "Reddit Fix") ---
        # Gibberish check
        if getattr(problem, 'is_gibberish', False):
            depth_score = 0
            impact_score = 0
            complexity_score = 0
            signal_quality = 0
            
        # Non-technical content check
        if not getattr(problem, 'is_technical', True):
            # Heavily cap all technical scores if content is personal/non-technical
            depth_score *= 0.1
            impact_score *= 0.1
            complexity_score *= 0.2
            signal_quality *= 0.3

        # --- Final EIS Calculation (0 - 100) ---
        # Weights: 0.35 Depth, 0.30 Impact, 0.20 Complexity, 0.15 Signal
        eis = (
            (0.35 * depth_score) +
            (0.30 * impact_score) +
            (0.20 * complexity_score) +
            (0.15 * signal_quality)
        ) * 100
        
        return {
            "technical_depth_score": round(depth_score, 3),
            "industry_impact_score": round(impact_score, 3),
            "cognitive_complexity_score": round(complexity_score, 3),
            "signal_quality_score": round(signal_quality, 3),
            "engineering_impact_score": round(eis, 2),
            "scoring_version": self.VERSION
        }

    def process_all_problems(self, db: Session):
        """Batch process all problems in the database"""
        problems = db.query(Problem).all()
        count = 0
        for problem in problems:
            scores = self.calculate_scores(problem)
            for attr, val in scores.items():
                setattr(problem, attr, val)
            count += 1
            if count % 50 == 0:
                db.commit()
                logger.info(f"Scored {count} problems...")
        
        db.commit()
        logger.info(f"Finished scoring all {count} problems.")
        return count

# Singleton instance access
_engine = None
def get_scoring_engine():
    global _engine
    if _engine is None:
        _engine = EngineeringImpactScoringEngine()
    return _engine

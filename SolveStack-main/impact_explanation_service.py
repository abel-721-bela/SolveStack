from models import Problem
from engineering_scoring_engine import get_scoring_engine

class ImpactExplanationService:
    def __init__(self):
        self.engine = get_scoring_engine()

    def explain_score(self, problem: Problem) -> dict:
        """
        Generate a human-readable explanation for why a problem scored its EIS.
        """
        depth = problem.technical_depth_score
        impact = problem.industry_impact_score
        complexity = problem.cognitive_complexity_score
        signal = problem.signal_quality_score
        eis = problem.engineering_impact_score
        
        reasons = []
        
        # Analyze Depth
        if depth > 0.6:
            reasons.append("high technical depth due to advanced engineering context (e.g., scaling, distributed systems)")
        elif depth > 0.3:
            reasons.append("solid technical context")
            
        # Analyze Impact
        if impact > 0.6:
            reasons.append("significant production-level impact and business risk markers")
        elif impact > 0.3:
            reasons.append("mentions of real-world system impact")
            
        # Analyze Complexity
        if complexity > 0.6:
            reasons.append("high cognitive load involving architectural trade-offs or complex decision making")
        elif complexity > 0.3:
            reasons.append("requires open-ended technical reasoning")
            
        # Analyze Signal
        if signal > 0.7:
            reasons.append("excellent signal clarity with specific technical constraints")
        elif signal < 0.4:
            reasons.append("low signal-to-noise ratio or primarily emotional tone")

        # Combine into summary
        if not reasons:
            summary = "This problem has low measurable engineering impact markers."
        else:
            if len(reasons) > 1:
                summary = f"This problem ranks high due to {', '.join(reasons[:-1])}, and {reasons[-1]}."
            else:
                summary = f"This problem ranks well due to {reasons[0]}."

        # Engineering Thinking Type
        thinking_type = "Standard Implementation"
        if complexity > 0.7:
            thinking_type = "Architectural / Strategic Reasoning"
        elif depth > 0.7:
            thinking_type = "Deep Systems Engineering"
        elif impact > 0.7:
            thinking_type = "Production Reliability / Risk Management"

        return {
            "problem_id": problem.ps_id,
            "engineering_impact_score": eis,
            "breakdown": {
                "depth": depth,
                "impact": impact,
                "complexity": complexity,
                "signal": signal
            },
            "explanation": summary,
            "thinking_type": thinking_type,
            "signals_contributed": self._get_contributing_signals(problem)
        }

    def _get_contributing_signals(self, problem: Problem) -> list:
        content = f"{problem.title} {problem.description}".lower()
        signals = []
        
        # Check specific groups
        for kw in self.engine.DEPTH_KEYWORDS:
            if kw in content:
                signals.append(f"Technical: {kw}")
        for kw in self.engine.IMPACT_KEYWORDS:
            if kw in content:
                signals.append(f"Impact: {kw}")
        for ph in self.engine.COMPLEXITY_PHRASES:
            if ph in content:
                signals.append(f"Cognitive: {ph}")
                
        return sorted(list(set(signals)))[:10] # Return unique top 10

# Singleton
_explanation_service = None
def get_explanation_service():
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ImpactExplanationService()
    return _explanation_service

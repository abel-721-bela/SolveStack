"""
Phase 2C: Intelligent Scoring & Matching Algorithms

This module contains heuristic-based algorithms for:
1. Problem Quality Scoring (0-100)
2. Skill-Problem Matching
3. Collaboration Suggestions

All algorithms are deterministic, explainable, and ML-free.
"""

from typing import List, Dict, Tuple
import re


# ============ FEATURE 1: Problem Quality Scoring ============

def score_description_quality(description: str) -> Tuple[int, List[str]]:
    """
    Scores description quality based on clarity and completeness (0-30 points).
    
    Heuristics:
    - Optimal length (100-500 chars): 10 pts
    - Technical keywords: up to 5 pts
    - Code snippets: 5 pts
    - Error messages: 5 pts
    - Questions/inquiry: 5 pts
    
    Returns: (score, reasons)
    """
    if not description:
        return 0, ["No description provided"]
    
    score = 0
    reasons = []
    length = len(description)
    
    # Optimal length
    if 100 <= length <= 500:
        score += 10
        reasons.append("Good description length")
    elif 50 <= length < 100:
        score += 5
        reasons.append("Adequate description length")
    elif length > 500:
        score += 7
        reasons.append("Detailed description")
    
    # Technical keywords
    tech_keywords = ['error', 'function', 'api', 'database', 'bug', 'crash', 'issue']
    tech_matches = sum(1 for kw in tech_keywords if kw.lower() in description.lower())
    tech_score = min(tech_matches, 5)
    score += tech_score
    if tech_score > 2:
        reasons.append(f"Technical depth ({tech_matches} keywords)")
    
    # Code snippets (backticks or indentation)
    if '```' in description or '`' in description:
        score += 5
        reasons.append("Includes code snippets")
    
    # Error messages
    if 'error:' in description.lower() or 'exception' in description.lower():
        score += 5
        reasons.append("Includes error details")
    
    # Shows inquiry
    if '?' in description:
        score += 5
        reasons.append("Clear questions asked")
    
    return min(score, 30), reasons


def score_technical_depth(suggested_tech: str, tags: List[str]) -> Tuple[int, List[str]]:
    """
    Measures technical complexity (0-25 points).
    
    Heuristics:
    - Number of technologies: up to 10 pts
    - Complex tech stack: 10 pts
    - Version specificity: 5 pts
    
    Returns: (score, reasons)
    """
    if not suggested_tech:
        return 5, ["Basic problem"]
    
    score = 0
    reasons = []
    
    # Count technologies
    tech_list = [t.strip() for t in suggested_tech.split(',') if t.strip()]
    tech_count = len(tech_list)
    tech_score = min(tech_count * 3, 10)
    score += tech_score
    if tech_count > 2:
        reasons.append(f"Multi-tech problem ({tech_count} technologies)")
    
    # Complexity indicators
    complex_techs = ['kubernetes', 'microservices', 'distributed', 'ml', 'ai', 'docker', 'cloud']
    tech_lower = suggested_tech.lower()
    if any(ct in tech_lower for ct in complex_techs):
        score += 10
        reasons.append("Advanced/complex technologies")
    
    # Version specificity
    if any(char.isdigit() for char in suggested_tech):
        score += 5
        reasons.append("Version-specific problem")
    
    return min(score, 25), reasons


def score_engagement(interested_count: int, upvotes: int, views: int) -> Tuple[int, List[str]]:
    """
    Measures community engagement (0-25 points).
    
    Heuristics:
    - Interested users: up to 10 pts
    - Upvotes: up to 10 pts
    - Views: up to 5 pts
    
    Returns: (score, reasons)
    """
    score = 0
    reasons = []
    
    # Interest
    interest_score = min(interested_count * 2, 10)
    score += interest_score
    if interested_count > 3:
        reasons.append(f"High interest ({interested_count} users)")
    
    # Upvotes
    upvote_score = min(upvotes, 10)
    score += upvote_score
    if upvotes > 5:
        reasons.append(f"Well-received ({upvotes} upvotes)")
    
    # Views
    if views > 100:
        score += 5
        reasons.append("High visibility")
    elif views > 50:
        score += 3
        reasons.append("Good visibility")
    elif views > 10:
        score += 1
    
    return min(score, 25), reasons


def score_reproducibility(description: str, reference_link: str) -> Tuple[int, List[str]]:
    """
    Evaluates how reproducible the problem is (0-20 points).
    
    Heuristics:
    - Has reference link: 10 pts
    - Mentions steps/setup: 5 pts
    - Has environment info: 5 pts
    
    Returns: (score, reasons)
    """
    score = 0
    reasons = []
    
    # Reference link
    if reference_link and reference_link.startswith('http'):
        score += 10
        reasons.append("Has reference link")
    
    # Reproduction steps
    repro_keywords = ['step', 'setup', 'install', 'run', 'reproduce', 'how to']
    desc_lower = description.lower() if description else ""
    if any(kw in desc_lower for kw in repro_keywords):
        score += 5
        reasons.append("Includes reproduction steps")
    
    # Environment info
    env_keywords = ['version', 'os', 'environment', 'python', 'node', 'npm', 'using']
    if any(kw in desc_lower for kw in env_keywords):
        score += 5
        reasons.append("Specifies environment")
    
    return min(score, 20), reasons


def classify_difficulty(quality_score: int, tech_depth_score: int, tech_count: int) -> str:
    """
    Classifies problem difficulty.
    
    Rules:
    - Beginner: Simple, single-tech, low complexity
    - Advanced: Complex systems, high quality/depth
    - Intermediate: Everything else
    """
    if tech_count == 1 and tech_depth_score < 10 and quality_score < 50:
        return 'Beginner'
    elif tech_depth_score >= 20 or quality_score >= 75:
        return 'Advanced'
    else:
        return 'Intermediate'


def estimate_effort(difficulty: str, tech_count: int) -> str:
    """
    Estimates time effort based on difficulty and scope.
    """
    if difficulty == 'Beginner':
        return '1-2 hours'
    elif difficulty == 'Intermediate':
        return '1-3 days' if tech_count < 3 else '3-7 days'
    else:  # Advanced
        return '1-2 weeks' if tech_count < 4 else '1+ month'


def compute_problem_quality_score(problem) -> Dict:
    """
    Computes overall quality score and classifications for a problem.
    
    Returns dict with:
    - quality_score (0-100)
    - difficulty (Beginner/Intermediate/Advanced)
    - estimated_effort (time estimate)
    - breakdown (component scores and reasons)
    """
    # Get interested count
    interested_count = len(problem.interested_users) if problem.interested_users else 0
    
    # Component scores
    desc_score, desc_reasons = score_description_quality(problem.description or "")
    tech_score, tech_reasons = score_technical_depth(problem.suggested_tech or "", problem.tags or [])
    engage_score, engage_reasons = score_engagement(interested_count, problem.upvotes, problem.views)
    repro_score, repro_reasons = score_reproducibility(problem.description or "", problem.reference_link or "")
    
    # Total quality score
    total_score = desc_score + tech_score + engage_score + repro_score
    
    # Tech count
    tech_count = len([t.strip() for t in (problem.suggested_tech or "").split(',') if t.strip()])
    
    # Classifications
    difficulty = classify_difficulty(total_score, tech_score, tech_count)
    effort = estimate_effort(difficulty, tech_count)
    
    return {
        "quality_score": total_score,
        "difficulty": difficulty,
        "estimated_effort": effort,
        "breakdown": {
            "description_quality": {"score": desc_score, "max": 30, "reasons": desc_reasons},
            "technical_depth": {"score": tech_score, "max": 25, "reasons": tech_reasons},
            "engagement": {"score": engage_score, "max": 25, "reasons": engage_reasons},
            "reproducibility": {"score": repro_score, "max": 20, "reasons": repro_reasons}
        }
    }


# ============ FEATURE 2: Skill-Problem Matching ============

def calculate_skill_match(user_skills: List[str], problem_tech: str) -> Tuple[int, List[str]]:
    """
    Calculates skill match score (0-40 points).
    
    Perfect match: All problem techs in user skills
    Partial match: Proportional to coverage
    """
    if not user_skills:
        return 0, ["No skills listed"]
    
    problem_techs = [t.strip().lower() for t in problem_tech.split(',') if t.strip()]
    if not problem_techs:
        return 10, ["General problem"]
    
    user_skills_lower = [s.lower() for s in user_skills]
    
    # Count matches (flexible matching - substring)
    matches = 0
    matched_techs = []
    for tech in problem_techs:
        if any(skill in tech or tech in skill for skill in user_skills_lower):
            matches += 1
            matched_techs.append(tech)
    
    match_ratio = matches / len(problem_techs)
    score = int(match_ratio * 40)
    
    reasons = []
    if match_ratio == 1.0:
        reasons.append("Perfect skill match")
    elif match_ratio >= 0.5:
        reasons.append(f"Strong match ({matches}/{len(problem_techs)} techs)")
    elif match_ratio > 0:
        reasons.append(f"Partial match ({matches}/{len(problem_techs)} techs)")
    else:
        reasons.append("Learning opportunity")
    
    return score, reasons


def calculate_difficulty_match(user_level: str, user_pref: str, problem_difficulty: str) -> Tuple[int, List[str]]:
    """
    Matches user level/preference to problem difficulty (0-20 points).
    """
    levels = {'Beginner': 0, 'Intermediate': 1, 'Advanced': 2}
    
    user_idx = levels.get(user_level, 1)
    pref_idx = levels.get(user_pref, 1)
    prob_idx = levels.get(problem_difficulty, 1)
    
    # Check against preference
    pref_diff = abs(pref_idx - prob_idx)
    
    reasons = []
    if pref_diff == 0:
        score = 20
        reasons.append("Perfect difficulty match")
    elif pref_diff == 1:
        score = 10
        reasons.append("Close difficulty match")
    else:
        score = 5
        reasons.append("Challenging difficulty")
    
    return score, reasons


def calculate_interest_match(user_interests: List[str], problem_tags: List[str], problem_desc: str) -> Tuple[int, List[str]]:
    """
    Matches user interests to problem domain (0-20 points).
    """
    if not user_interests:
        return 10, []  # Neutral
    
    score = 0
    reasons = []
    matched_interests = []
    
    for interest in user_interests:
        interest_lower = interest.lower()
        
        # Check in tags
        if problem_tags and any(interest_lower in tag.lower() for tag in problem_tags):
            score += 10
            matched_interests.append(interest)
        
        # Check in description
        elif problem_desc and interest_lower in problem_desc.lower():
            score += 5
            matched_interests.append(interest)
    
    if matched_interests:
        reasons.append(f"Matches interests: {', '.join(matched_interests[:2])}")
    
    return min(score, 20), reasons


def calculate_novelty_score(user, problem) -> Tuple[int, List[str]]:
    """
    Balance between familiar and novel (0-20 points).
    
    - Already interested: -5 pts (encourage exploration)
    - Completely new: +15 pts (learning opportunity)
    - Some familiarity: +10 pts (optimal)
    """
    score = 10  # Base
    reasons = []
    
    # Penalize if already interested
    if user in problem.interested_users:
        score -= 5
        reasons.append("Already tracking this problem")
    else:
        score += 10
        reasons.append("New discovery")
    
    return max(score, 0), reasons


def compute_match_score(user, problem) -> Dict:
    """
    Computes overall match score for user-problem pair.
    
    Returns dict with:
    - match_score (0-100)
    - reasons (human-readable)
    - breakdown (component scores)
    """
    skill_score, skill_reasons = calculate_skill_match(user.skills or [], problem.suggested_tech or "")
    diff_score, diff_reasons = calculate_difficulty_match(
        user.experience_level or "Intermediate",
        user.preferred_difficulty or "Intermediate",
        problem.difficulty or "Intermediate"
    )
    interest_score, interest_reasons = calculate_interest_match(
        user.interests or [],
        problem.tags or [],
        problem.description or ""
    )
    novelty_score, novelty_reasons = calculate_novelty_score(user, problem)
    
    total_score = skill_score + diff_score + interest_score + novelty_score
    
    # Combine all reasons
    all_reasons = skill_reasons + diff_reasons + interest_reasons + novelty_reasons
    
    return {
        "match_score": total_score,
        "reasons": all_reasons,
        "breakdown": {
            "skill_match": skill_score,
            "difficulty_match": diff_score,
            "interest_match": interest_score,
            "novelty": novelty_score
        }
    }


# ============ FEATURE 3: Collaboration Suggestions ============

def calculate_skill_complementarity(user_a_skills: List[str], user_b_skills: List[str], problem_tech: str) -> Tuple[int, List[str]]:
    """
    Scores how well two users' skills complement each other (0-35 points).
    
    Best scenario: Together they cover all problem techs
    """
    if not user_a_skills or not user_b_skills:
        return 10, ["Limited skill information"]
    
    problem_techs = set(t.strip().lower() for t in problem_tech.split(',') if t.strip())
    if not problem_techs:
        return 15, ["General collaboration"]
    
    a_skills_lower = [s.lower() for s in user_a_skills]
    b_skills_lower = [s.lower() for s in user_b_skills]
    
    # What each user covers
    a_matches = {tech for tech in problem_techs if any(skill in tech or tech in skill for skill in a_skills_lower)}
    b_matches = {tech for tech in problem_techs if any(skill in tech or tech in skill for skill in b_skills_lower)}
    
    # Combined coverage
    combined_coverage = len(a_matches | b_matches) / len(problem_techs)
    
    # Unique contribution from user B
    unique_contribution = len(b_matches - a_matches) / len(problem_techs) if problem_techs else 0
    
    score = int((combined_coverage * 25) + (unique_contribution * 10))
    
    reasons = []
    if combined_coverage >= 0.8:
        reasons.append("Comprehensive skill coverage together")
    if unique_contribution > 0.3:
        reasons.append("Brings complementary skills")
    
    return min(score, 35), reasons


def calculate_experience_balance(user_a_level: str, user_b_level: str, problem_diff: str) -> Tuple[int, List[str]]:
    """
    Evaluates experience balance (0-20 points).
    
    Ideal: Mix of levels OR both match problem
    """
    levels_map = {'Beginner': 0, 'Intermediate': 1, 'Advanced': 2}
    
    a_idx = levels_map.get(user_a_level, 1)
    b_idx = levels_map.get(user_b_level, 1)
    prob_idx = levels_map.get(problem_diff, 1)
    
    reasons = []
    
    # Both match problem
    if a_idx == prob_idx and b_idx == prob_idx:
        score = 20
        reasons.append("Both match problem difficulty")
    # One matches, one helps
    elif (a_idx == prob_idx and abs(b_idx - prob_idx) <= 1) or \
         (b_idx == prob_idx and abs(a_idx - prob_idx) <= 1):
        score = 15
        reasons.append("Good experience balance")
    # Mentorship opportunity
    elif abs(a_idx - b_idx) >= 1:
        score = 12
        reasons.append("Mentorship opportunity")
    else:
        score = 8
    
    return score, reasons


def calculate_activity_compatibility(user_a_activity: int, user_b_activity: int) -> Tuple[int, List[str]]:
    """
    Checks if both users are active (0-25 points).
    
    Both active → Better collaboration
    """
    avg_activity = (user_a_activity + user_b_activity) / 2
    activity_gap = abs(user_a_activity - user_b_activity)
    
    score = int(avg_activity * 0.2)  # Max 20 from average
    
    reasons = []
    if avg_activity > 70:
        reasons.append("Both highly active")
    elif avg_activity > 40:
        reasons.append("Good activity levels")
    
    # Penalty for large gap
    if activity_gap > 40:
        score -= 10
        reasons.append("Activity mismatch")
    
    return max(min(score, 25), 0), reasons


def calculate_past_success(user_a, user_b) -> Tuple[int, List[str]]:
    """
    Checks past collaboration history (0-20 points).
    
    First time: Neutral (10 pts)
    Past collaboration: Bonus points
    """
    # Check shared groups
    a_groups = set(user_a.joined_collaboration_groups) if hasattr(user_a, 'joined_collaboration_groups') else set()
    b_groups = set(user_b.joined_collaboration_groups) if hasattr(user_b, 'joined_collaboration_groups') else set()
    
    shared_groups = a_groups & b_groups
    
    reasons = []
    if len(shared_groups) > 0:
        score = min(20, 10 + len(shared_groups) * 5)
        reasons.append(f"Past collaborations ({len(shared_groups)})")
    else:
        score = 10  # Neutral for new pairs
    
    return score, reasons


def compute_compatibility_score(user_a, user_b, problem) -> Dict:
    """
    Computes compatibility score between two users for a problem.
    
    Returns dict with:
    - compatibility_score (0-100)
    - reasons (human-readable)
    - breakdown (component scores)
    """
    skill_comp, skill_reasons = calculate_skill_complementarity(
        user_a.skills or [],
        user_b.skills or [],
        problem.suggested_tech or ""
    )
    exp_balance, exp_reasons = calculate_experience_balance(
        user_a.experience_level or "Intermediate",
        user_b.experience_level or "Intermediate",
        problem.difficulty or "Intermediate"
    )
    activity_comp, activity_reasons = calculate_activity_compatibility(
        user_a.activity_score or 50,
        user_b.activity_score or 50
    )
    past_success, past_reasons = calculate_past_success(user_a, user_b)
    
    total_score = skill_comp + exp_balance + activity_comp + past_success
    
    all_reasons = skill_reasons + exp_reasons + activity_reasons + past_reasons
    
    return {
        "compatibility_score": total_score,
        "reasons": all_reasons,
        "breakdown": {
            "skill_complementarity": skill_comp,
            "experience_balance": exp_balance,
            "activity_compatibility": activity_comp,
            "past_success": past_success
        }
    }

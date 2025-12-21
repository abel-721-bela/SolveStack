"""
Script to add sample user profiles and update problem scores for Phase 2C testing.
"""

from database import SessionLocal
from models import User, Problem
from datetime import datetime

def update_user_profiles():
    """Add skills, interests, and preferences to existing users for testing."""
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("⚠️ No users found. Register some users first!")
            return
        
        # Sample profiles for testing
        sample_profiles = [
            {
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "experience_level": "Advanced",
                "interests": ["Backend Development", "API Design"],
                "activity_score": 85,
                "preferred_difficulty": "Advanced",
                "preferred_effort": "1-2 weeks"
            },
            {
                "skills": ["React", "JavaScript", "Material-UI"],
                "experience_level": "Intermediate",
                "interests": ["Frontend Development", "UI/UX"],
                "activity_score": 70,
                "preferred_difficulty": "Intermediate",
                "preferred_effort": "1-3 days"
            },
            {
                "skills": ["Docker", "Kubernetes", "DevOps"],
                "experience_level": "Advanced",
                "interests": ["DevOps", "Cloud Infrastructure"],
                "activity_score": 90,
                "preferred_difficulty": "Advanced",
                "preferred_effort": "3-7 days"
            },
            {
                "skills": ["Python", "Machine Learning", "TensorFlow"],
                "experience_level": "Intermediate",
                "interests": ["Machine Learning", "Data Science"],
                "activity_score": 60,
                "preferred_difficulty": "Intermediate",
                "preferred_effort": "1-2 weeks"
            },
            {
                "skills": ["JavaScript", "Node.js", "Express"],
                "experience_level": "Beginner",
                "interests": ["Web Development", "Backend Development"],
                "activity_score": 40,
                "preferred_difficulty": "Beginner",
                "preferred_effort": "1-2 hours"
            }
        ]
        
        # Update users with sample profiles (cycle through profiles)
        for i, user in enumerate(users):
            profile = sample_profiles[i % len(sample_profiles)]
            
            user.skills = profile["skills"]
            user.experience_level = profile["experience_level"]
            user.interests = profile["interests"]
            user.activity_score = profile["activity_score"]
            user.preferred_difficulty = profile["preferred_difficulty"]
            user.preferred_effort = profile["preferred_effort"]
            
            print(f"✅ Updated profile for {user.username}: {profile['skills']}")
        
        db.commit()
        print(f"\n🎉 Successfully updated {len(users)} user profiles!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


def score_all_problems():
    """Compute quality scores for all problems using the scoring engine."""
    from scoring_engine import compute_problem_quality_score
    
    db = SessionLocal()
    
    try:
        problems = db.query(Problem).all()
        
        if not problems:
            print("⚠️ No problems found. Run scraping or add sample problems first!")
            return
        
        scored_count = 0
        
        for problem in problems:
            # Compute score
            result = compute_problem_quality_score(problem)
            
            # Update problem
            problem.quality_score = result["quality_score"]
            problem.difficulty = result["difficulty"]
            problem.estimated_effort = result["estimated_effort"]
            problem.score_updated_at = datetime.utcnow()
            
            scored_count += 1
            print(f"✅ Scored #{problem.ps_id}: {result['quality_score']}/100 ({result['difficulty']})")
        
        db.commit()
        print(f"\n🎉 Successfully scored {scored_count} problems!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 2C: Sample Data Setup")
    print("=" * 60)
    
    print("\n📋 Step 1: Updating user profiles...")
    update_user_profiles()
    
    print("\n📊 Step 2: Scoring all problems...")
    score_all_problems()
    
    print("\n" + "=" * 60)
    print("✅ Phase 2C setup complete!")
    print("=" * 60)
    print("\n💡 You can now test:")
    print("   - POST /problems/{id}/score")
    print("   - GET /recommendations")
    print("   - GET /collaborate/suggestions/{id}")
    print("\nOpen Swagger UI: http://localhost:8000/docs")

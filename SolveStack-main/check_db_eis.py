from database import SessionLocal
from models import Problem
import json

def check():
    db = SessionLocal()
    try:
        probs = db.query(Problem).limit(5).all()
        results = []
        for p in probs:
            results.append({
                "id": p.ps_id,
                "eis": p.engineering_impact_score,
                "diff_score": p.difficulty_score,
                "diff_level": p.difficulty_level
            })
        with open("output.json", "w") as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        with open("output.json", "w") as f:
            json.dump({"error": str(e)}, f)
    finally:
        db.close()

if __name__ == '__main__':
    check()

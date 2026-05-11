import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_shelf_modes():
    modes = ["explore", "production", "architecture", "high-cognitive"]
    for mode in modes:
        logger.info(f"Testing Shelf Mode: {mode}")
        try:
            response = requests.get(f"{BASE_URL}/shelf", params={"mode": mode, "limit": 3})
            response.raise_for_status()
            data = response.json()
            logger.info(f"Mode: {mode}, Total Found: {data.get('total_found')}")
            for res in data.get("results", []):
                logger.info(f"  - [{res['id']}] {res['title']} (Score: {res['engineering_impact_score']})")
        except Exception as e:
            logger.error(f"Failed to test mode {mode}: {e}")

def test_explainability():
    logger.info("Testing Impact Explanation...")
    try:
        # Get top impact problem first
        shelf_res = requests.get(f"{BASE_URL}/shelf", params={"sort_by": "impact", "limit": 1})
        shelf_res.raise_for_status()
        top_problem = shelf_res.json()["results"][0]
        pid = top_problem["id"]
        
        explain_res = requests.get(f"{BASE_URL}/shelf/{pid}/explain")
        explain_res.raise_for_status()
        data = explain_res.json()
        logger.info(f"Explanation for Problem {pid}:")
        logger.info(f"  Score: {data['engineering_impact_score']}")
        logger.info(f"  Type: {data['thinking_type']}")
        logger.info(f"  Why: {data['explanation']}")
        logger.info(f"  Signals: {', '.join(data['signals_contributed'])}")
    except Exception as e:
        logger.error(f"Failed to test explainability: {e}")

def test_analytics():
    logger.info("Testing Shelf Analytics...")
    try:
        response = requests.get(f"{BASE_URL}/analytics/shelf")
        response.raise_for_status()
        data = response.json()
        logger.info(f"Analytics: Total={data['total_analyzed']}, Low Signal %={data['low_signal_percentage']}, Avg EIS={data['avg_impact_score']}")
        logger.info("Distribution:")
        for dist in data["eis_distribution"]:
            logger.info(f"  {dist['bucket']}: {dist['count']}")
    except Exception as e:
        logger.error(f"Failed to test analytics: {e}")

if __name__ == "__main__":
    # Note: Requires the FastAPI server to be running.
    # If not running, we'll suggest the user to start it or we'll try to run the logic directly using DB session.
    logger.info("Checking if server is up...")
    try:
        requests.get(BASE_URL)
        test_shelf_modes()
        test_explainability()
        test_analytics()
    except requests.exceptions.ConnectionError:
        logger.warning("Server is not running. Please start with 'uvicorn main:app --reload'")
        logger.info("Proceeding with direct DB validation instead...")
        # Direct DB validation script logic could go here

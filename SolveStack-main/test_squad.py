from fastapi.testclient import TestClient
from main import app
import traceback

client = TestClient(app)

try:
    response = client.get("/squads")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print("Exception occurred!")
    traceback.print_exc()

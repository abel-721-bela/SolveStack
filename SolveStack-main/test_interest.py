"""Test interest feature end-to-end."""
import urllib.request, json, sys

BASE = "http://localhost:8000"

def api(method, path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.getcode(), json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# Step 1: Register a fresh test user
print("--- 1. Registering test user ---")
code, data = api("POST", "/auth/register", {"username": "interesttest99", "email": "interesttest99@test.com", "password": "TestPass123!"})
print(f"  Register: {code} -> {data}")

# Step 2: Login
print("\n--- 2. Logging in ---")
code, data = api("POST", "/auth/login", {"username": "interesttest99", "password": "TestPass123!"})
print(f"  Login: {code} -> {list(data.keys())}")
token = data.get("access_token")
if not token:
    print("  ERROR: No token! Aborting.")
    sys.exit(1)
print(f"  Got token: {token[:30]}...")

# Step 3: Get first problem ID
print("\n--- 3. Getting first problem ---")
code, data = api("GET", "/problems?skip=0&limit=1")
prob = data[0] if data else None
prob_id = prob.get("id") if prob else None
print(f"  Problem ID: {prob_id}, title: {(prob or {}).get('title', '')[:50]}")

# Step 4: Try to mark interest
print(f"\n--- 4. Marking interest on problem {prob_id} ---")
code, data = api("POST", "/interest", {"problem_id": int(prob_id)}, token=token)
print(f"  POST /interest: {code} -> {data}")

# Step 5: Get /me to see if interest registered
print("\n--- 5. Checking /me/interests ---")
code, data = api("GET", "/me/interests", token=token)
print(f"  GET /me/interests: {code} -> {len(data) if isinstance(data, list) else data} item(s)")

# Step 6: Get /me profile
print("\n--- 6. Checking /me profile ---")
code, data = api("GET", "/me", token=token)
print(f"  GET /me: {code} -> interested_count={data.get('interested_count')}, interests={data.get('interests')}")

# Step 7: Remove interest
print(f"\n--- 7. Removing interest on problem {prob_id} ---")
code, data = api("DELETE", f"/interest/{prob_id}", token=token)
print(f"  DELETE /interest/{prob_id}: {code} -> {data}")

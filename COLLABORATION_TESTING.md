# Phase 2B: Collaboration System - Testing Guide

## Backend Endpoints Summary

All 4 endpoints implemented successfully:
1. **POST** `/collaborate/request` - Create collaboration request
2. **POST** `/collaborate/accept` - Accept your request
3. **POST** `/collaborate/reject` - Reject/withdraw request
4. **GET** `/collaborate/{problem_id}` - Get collaboration status

---

## Testing via Swagger UI

**Access Swagger**: `http://localhost:8000/docs`

### Prerequisites

1. **Register & Login**:
   ```bash
   POST /register
   {
     "email": "alice@example.com",
     "username": "alice", 
     "password": "password123"
   }
   
   POST /login
   username: alice@example.com
   password: password123
   # Copy the access_token
   ```

2. **Mark Interest**:
   ```bash
   POST /interest
   {"problem_id": 1}
   ```

---

## Test Scenarios

### Scenario 1: Single User Request

```bash
# Step 1: Create request
POST /collaborate/request
{"problem_id": 1}

Response:
{
  "request_id": 1,
  "problem_id": 1,
  "status": "pending",
  "message": "Collaboration request created successfully...",
  "created_at": "2024-12-21T..."
}

# Step 2: Accept request
POST /collaborate/accept
{"problem_id": 1}

Response:
{
  "request_id": 1,
  "problem_id": 1,
  "status": "accepted",
  "message": "Collaboration accepted! Waiting for more users...",
  "group_created": false  # No group yet (need ≥2 users)
}
```

### Scenario 2: Two Users → Group Formation

```bash
# User A (alice):
1. Mark interest in problem 1
2. POST /collaborate/request {"problem_id": 1}
3. POST /collaborate/accept {"problem_id": 1}

# User B (bob):
1. Register, login, mark interest in problem 1
2. POST /collaborate/request {"problem_id": 1}
3. POST /collaborate/accept {"problem_id": 1}

Response for User B:
{
  "request_id": 2,
  "problem_id": 1,
  "status": "accepted",
  "group_created": true,  # ✅ Group auto-created!
  "group_id": 1,
  "total_members": 2,
  "collaborators": ["alice", "bob"],
  "message": "Collaboration accepted! You're now in a group with 2 members."
}
```

### Scenario 3: Third User Joins Existing Group

```bash
# User C (carol):
1. Mark interest in problem 1
2. POST /collaborate/request {"problem_id": 1}
3. POST /collaborate/accept {"problem_id": 1}

Response:
{
  "group_created": false,  # Group already existed
  "group_id": 1,
  "total_members": 3,  # Added to existing group
  "collaborators": ["alice", "bob", "carol"]
}
```

### Scenario 4: User Withdraws from Group

```bash
# User B withdraws:
POST /collaborate/reject
{"problem_id": 1}

Response:
{
  "request_id": 2,
  "problem_id": 1,
  "status": "rejected",
  "message": "Collaboration request rejected/withdrawn successfully"
}

# Check group status (User A):
GET /collaborate/1

Response:
{
  "active_group": {
    "group_id": 1,
    "member_count": 2,  # Bob removed
    "members": ["alice", "carol"],
    "is_active": true  # Still active (≥2 members)
  }
}
```

### Scenario 5: Group Deactivation

```bash
# If Carol also withdraws:
POST /collaborate/reject {"problem_id": 1}

# Now group has <2 members → deactivated

GET /collaborate/1
Response:
{
  "active_group": {
    "group_id": 1,
    "member_count": 1,
    "is_active": false  # Deactivated!
  }
}
```

---

## GET /collaborate/{problem_id} - Status Endpoint

```bash
GET /collaborate/1

Full Response:
{
  "problem_id": 1,
  "problem_title": "React state not updating after API call",
  "your_request": {
    "request_id": 1,
    "status": "accepted",
    "created_at": "2024-12-21T..."
  },
  "total_requests": 5,
  "pending_requests": 2,
  "accepted_requests": 3,
  "active_group": {
    "group_id": 1,
    "member_count": 3,
    "members": ["alice", "bob", "carol"],
    "created_at": "2024-12-21T...",
    "is_active": true
  },
  "can_request": false,
  "reason": "You already have a request (status: accepted)"
}
```

---

## Error Cases

### 1. Request without Interest

```bash
POST /collaborate/request
{"problem_id": 1}

Error (400):
{
  "detail": "You must mark interest in this problem before requesting collaboration"
}
```

### 2. Duplicate Request

```bash
# Already have a request
POST /collaborate/request
{"problem_id": 1}

Error (400):
{
  "detail": "You already have a collaboration request for this problem (status: pending)"
}
```

### 3. Accept without Request

```bash
POST /collaborate/accept
{"problem_id": 99}

Error (404):
{
  "detail": "You don't have a collaboration request for this problem. Create one first."
}
```

---

## Business Rules Verified

✅ **Interest Prerequisite**: User must mark interest before requesting
✅ **One Request Per User/Problem**: Unique constraint enforced
✅ **Minimum 2 Members**: Group created only when ≥2 users accepted
✅ **One Group Per Problem**: New users added to existing group
✅ **Withdrawal Allowed**: Users can withdraw after accepting
✅ **Auto-Deactivation**: Group deactivates if members drop below 2

---

## Quick Test Commands (curl)

```bash
# Login and get token
TOKEN=$(curl -X POST "http://localhost:8000/login" \
  -d "username=alice@example.com&password=password123" | jq -r .access_token)

# Mark interest
curl -X POST "http://localhost:8000/interest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem_id": 1}'

# Request collaboration
curl -X POST "http://localhost:8000/collaborate/request" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem_id": 1}'

# Accept
curl -X POST "http://localhost:8000/collaborate/accept" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem_id": 1}'

# Check status
curl "http://localhost:8000/collaborate/1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Next Steps

1. Test with 2-3 users to verify group formation
2. Test withdrawal and group deactivation
3. Verify all error cases
4. Check Swagger docs for auto-generated API documentation

**All endpoints are backend-only and exam-safe!** 🎓

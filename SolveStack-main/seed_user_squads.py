"""
Seed script: Add u@example.com (user id=12) to several squads
and populate those squads with realistic chat history.
"""

from database import SessionLocal
from models import User, CollaborationGroup, group_members, SquadMessage, SquadJoinRequest
from datetime import datetime, timedelta
import random

db = SessionLocal()

TARGET_EMAIL = "u@example.com"
TARGET_SQUAD_IDS = [1, 2, 7]   # squads the user will join as member

user = db.query(User).filter(User.email == TARGET_EMAIL).first()
if not user:
    print(f"[!] User {TARGET_EMAIL} not found – aborting.")
    db.close()
    exit(1)

print(f"[+] Found user: {user.username}  (id={user.id})")

# ── 1. Join the target squads ──────────────────────────────────────────────────
for squad_id in TARGET_SQUAD_IDS:
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad:
        print(f"  [!] Squad {squad_id} not found, skipping.")
        continue

    already = any(m.id == user.id for m in squad.members)
    if already:
        print(f"  [=] Already in squad {squad_id} ({squad.name}), skipping.")
    else:
        squad.members.append(user)
        # Mark any pending join request as accepted
        req = db.query(SquadJoinRequest).filter(
            SquadJoinRequest.squad_id == squad_id,
            SquadJoinRequest.user_id == user.id
        ).first()
        if req:
            req.status = "accepted"
        print(f"  [+] Added to squad {squad_id} ({squad.name})")

db.commit()

# ── 2. Seed realistic chat messages ───────────────────────────────────────────

SQUAD_CHAT_SEEDS = {
    1: [  # Scalability Hackers
        (2,  "Hey team, let's tackle the Redis bottleneck first. Anyone looked at the Lua scripts?"),
        (12, "I was reading about pipelining + connection pooling — could cut latency by ~40%."),
        (2,  "Nice! I'll spin up a bench tonight. Can you share the article?"),
        (12, "Sure, posting the link now. Also found a blog about consistent hashing for sharding."),
        (2,  "Perfect. Let's do a sync call tomorrow at 10 AM UTC?"),
        (12, "Works for me. I'll prepare a short deck on the architecture options."),
        (2,  "Awesome. Meanwhile I'll profile the write path on staging."),
        (12, "Sounds good. By the way I noticed the connection pool size is still at default 10 — should we bump it?"),
        (2,  "Yeah let's try 50 first and measure. Don't want to overload the DB."),
        (12, "Makes sense, I'll open a PR for that config change now."),
    ],
    2: [  # ML Pipeline Builders
        (2,  "Anyone figured out the feature drift issue in prod?"),
        (12, "Yeah, looks like the upstream schema changed and one column is now float64 instead of int32."),
        (2,  "Classic. Did you fix it in the ingestion layer?"),
        (12, "Added a cast + alert. Also added a schema contract test so this won't sneak in again."),
        (2,  "Smart. What about the model retraining schedule — still weekly?"),
        (12, "I think we should switch to triggered retraining when drift exceeds 0.05 KL divergence."),
        (2,  "Agreed. I'll write the monitoring hook. Can you update the model registry API?"),
        (12, "On it. ETA end of day."),
        (2,  "Great, let's ship this by Thursday."),
        (12, "👍 I'll open the tracking issue now."),
    ],
    7: [  # API Gateway Rangers
        (7,  "Welcome everyone! Let's start by mapping all the failing routes."),
        (3,  "I've seen 504s on /api/v2/recommendations — probably the upstream timeout config."),
        (7,  "Good catch. The default is 30s but recommendations service can take 45s on cold start."),
        (12, "We should add a circuit breaker too. Failing fast is better than hanging requests."),
        (7,  "Totally agree. I'll add resilience4j config for that route."),
        (3,  "Meanwhile I'll bump the timeout to 60s on the gateway level as a short-term fix."),
        (12, "And we should propagate correlation IDs so tracing works end-to-end."),
        (7,  "Yes! X-Request-ID header. I'll make it standard across all services."),
        (3,  "I can add it to the middleware layer. Should take an hour."),
        (12, "Let's also document this in the runbook so on-call engineers know what to check."),
        (7,  "Great idea. I'll set up a Notion page for it."),
        (12, "Ping me when it's ready, I'll add the tracing section."),
    ],
}

base_time = datetime.utcnow() - timedelta(hours=6)

for squad_id, convo in SQUAD_CHAT_SEEDS.items():
    # Delete old seeded messages to avoid duplicates
    existing = db.query(SquadMessage).filter(SquadMessage.squad_id == squad_id).count()
    if existing >= len(convo):
        print(f"  [=] Squad {squad_id} already has {existing} messages, skipping seed.")
        continue

    print(f"  [+] Seeding {len(convo)} messages into squad {squad_id}...")
    for i, (sender_id, content) in enumerate(convo):
        # Check sender exists
        sender = db.query(User).filter(User.id == sender_id).first()
        if not sender:
            print(f"    [!] Sender id={sender_id} not found, skipping message.")
            continue
        msg = SquadMessage(
            squad_id=squad_id,
            sender_id=sender_id,
            content=content,
            sent_at=base_time + timedelta(minutes=i * random.randint(2, 8)),
        )
        db.add(msg)

db.commit()
print("\n[✓] Done! User is now in squads and chat history is seeded.")
db.close()

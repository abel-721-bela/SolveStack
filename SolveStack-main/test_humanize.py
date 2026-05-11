"""Test humanize_problem for PS#226."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import engine
from sqlalchemy import text
from humanize_service import humanize_problem

print("Testing humanize_problem for PS#226...")
conn = engine.connect()
row = conn.execute(text("SELECT title, description FROM problems WHERE ps_id = 226")).fetchone()
title, desc = row

print(f"Title: {title}")
print(f"Description length: {len(desc or '')}")

explanation, provider = humanize_problem(title or "", desc or "")
print(f"Provider: {provider}")
print(f"Explanation: {explanation}")
conn.close()

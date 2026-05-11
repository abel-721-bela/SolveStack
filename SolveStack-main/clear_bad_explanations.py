"""Force regenerate specific problems."""
from database import engine
from sqlalchemy import text

print("Forcing regeneration for known bad PS_IDs...")
conn = engine.connect()
conn.execute(text("UPDATE problems SET humanized_explanation = NULL WHERE ps_id IN (226, 231)"))
conn.commit()
conn.close()
print("Cleared humanized_explanation for PS#226, 231. Now running regen...")

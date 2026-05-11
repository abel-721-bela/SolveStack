
import sqlite3

try:
    conn = sqlite3.connect('solvestack.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    mode = cursor.fetchone()[0]
    print(f"WAL mode enabled. Current mode: {mode}")
    conn.close()
except Exception as e:
    print(f"Error checking DB: {e}")

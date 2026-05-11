import sqlite3
import os

def check_raw_db():
    db_path = "c:\\Users\\stuvs\\Solvestack\\SolveStack-main\\solvestack.db"
    if not os.path.exists(db_path):
        print(f"Error: DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- RAW DATABASE CHECK (FIXED) ---")
    
    # Check users
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    print(f"\nUsers ({len(users)}):")
    for u in users:
        print(f"  ID: {u[0]} | Name: {u[1]} | Email: {u[2]}")
        
    # Check problem_interests table
    cursor.execute("SELECT user_id, problem_id FROM problem_interests")
    interests = cursor.fetchall()
    print(f"\nProblem Interests Records ({len(interests)}):")
    for i in interests:
        print(f"  User ID: {i[0]} | Problem ID: {i[1]}")
    
    conn.close()
    print("\n--- END RAW CHECK ---")

if __name__ == "__main__":
    check_raw_db()

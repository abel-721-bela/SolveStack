import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_db():
    try:
        # Connect to default postgres database to create our database
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='1234',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create database
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'solvestack'")
        exists = cur.fetchone()
        if not exists:
            print("Creating database solvestack...")
            cur.execute("CREATE DATABASE solvestack")
        else:
            print("Database solvestack already exists.")
            
        cur.close()
        conn.close()
        
        # Connect to solvestack database to create extension
        conn = psycopg2.connect(
            dbname='solvestack',
            user='postgres',
            password='1234',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Creating pgvector extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        cur.close()
        conn.close()
        print("Setup complete.")
        
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == '__main__':
    setup_db()

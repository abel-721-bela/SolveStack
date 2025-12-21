"""
Add this endpoint to verify which database is actually being used.
This will help confirm PostgreSQL connection through the API.
"""

# Add this to main.py to verify database connection

@app.get("/db-info", tags=["Debug"])
def get_database_info(db: Session = Depends(get_db)):
    """
    Debug endpoint: Show which database is actually being used.
    
    Returns database URL and type (SQLite vs PostgreSQL).
    """
    from database import engine
    from sqlalchemy import inspect
    
    # Get database URL
    db_url = str(engine.url)
    
    # Determine database type
    if "postgresql" in db_url:
        db_type = "PostgreSQL"
    elif "sqlite" in db_url:
        db_type = "SQLite"
    else:
        db_type = "Unknown"
    
    # Count tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    return {
        "database_type": db_type,
        "database_url": db_url.split("@")[-1] if "@" in db_url else db_url,  # Hide password
        "total_tables": len(tables),
        "tables": sorted(tables),
        "status": "🎉 Production Ready!" if db_type == "PostgreSQL" else "⚠️ Development Mode"
    }

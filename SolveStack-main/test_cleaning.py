from cleaning_layer import DataCleaner
from datetime import datetime

cleaner = DataCleaner()
raw = {
    "source": "test",
    "source_id": "1",
    "author_name": "user",
    "author_id": "1",
    "reference_link": "http://example.com/1",
    "date": "2024-01-01",
    "raw_title": "Test Problem with <b>HTML</b>",
    "raw_description": "Description with ```python\nprint('code')\n```",
    "raw_tags": ["python", "react"]
}

try:
    cleaned = cleaner.clean_problem(raw)
    print("Successfully cleaned problem")
    import json
    # Use a custom encoder for datetime objects if needed, but for print just omit them
    # print(json.dumps({k:v for k,v in cleaned.items() if not isinstance(v, (datetime, datetime.date))}, indent=2))
    print(f"Title: {cleaned['title']}")
    print(f"Tags: {cleaned['tags']}")
    print(f"Difficulty Score: {cleaned['difficulty_score']}")
except Exception as e:
    print(f"Error cleaning problem: {e}")
    import traceback
    traceback.print_exc()

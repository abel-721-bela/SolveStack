import requests
import json

# Query the database
response = requests.get("http://localhost:8000/problems?limit=100")
problems = response.json()

# Write to file
with open('db_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"\n{'='*60}\n")
    f.write(f"DATABASE VERIFICATION REPORT\n")
    f.write(f"{'='*60}\n\n")

    # Count by source
    source_counts = {}
    for problem in problems:
        source = problem.get('source', 'unknown')
        source_prefix = source.split('/')[0]  # Get 'reddit', 'stackoverflow', or 'hackernews'
        source_counts[source_prefix] = source_counts.get(source_prefix, 0) + 1

    f.write(f"📊 Total Problems in Database: {len(problems)}\n\n")
    f.write(f"Problems by Source:\n")
    for source, count in sorted(source_counts.items()):
        f.write(f"  • {source.capitalize()}: {count} problems\n")

    f.write(f"\n{'='*60}\n")
    f.write(f"SAMPLE PROBLEMS FROM EACH SOURCE:\n")
    f.write(f"{'='*60}\n\n")

    # Show sample from each source
    shown_sources = set()
    for problem in problems:
        source = problem.get('source', 'unknown')
        source_prefix = source.split('/')[0]
        
        if source_prefix not in shown_sources:
            shown_sources.add(source_prefix)
            f.write(f"\n{source_prefix.upper()} EXAMPLE:\n")
            f.write(f"  Title: {problem.get('title', 'N/A')[:80]}...\n")
            f.write(f"  Source: {problem.get('source', 'N/A')}\n")
            f.write(f"  Source ID: {problem.get('source_id', 'N/A')}\n")
            f.write(f"  Tech: {problem.get('suggested_tech', 'N/A')}\n")
            f.write(f"  Link: {problem.get('reference_link', 'N/A')[:60]}...\n")
            f.write(f"  Solution Type: {problem.get('solution_possibility', 'N/A')}\n")
            f.write(f"  Has Explanation: {'Yes' if problem.get('humanized_explanation') else 'No'}\n")

    f.write(f"\n{'='*60}\n")
    f.write(f"FIELD VALIDATION:\n")
    f.write(f"{'='*60}\n\n")

    # Check if all problems have required fields
    required_fields = ['title', 'description', 'source', 'source_id', 'humanized_explanation', 'solution_possibility']
    missing_fields = {}

    for problem in problems:
        for field in required_fields:
            if not problem.get(field):
                if field not in missing_fields:
                    missing_fields[field] = 0
                missing_fields[field] += 1

    if missing_fields:
        f.write("⚠️  Some problems are missing required fields:\n")
        for field, count in missing_fields.items():
            f.write(f"  • {count} problems missing '{field}'\n")
    else:
        f.write("✅ All problems have all required fields!\n")

    f.write(f"\n{'='*60}\n\n")

print("✅ Report saved to db_report.txt")


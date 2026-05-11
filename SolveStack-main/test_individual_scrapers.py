"""
Test individual scrapers to diagnose why Reddit and Stack Overflow return 0 problems
"""
import sys

# Redirect output to file
output_file = open('scraper_test_results.txt', 'w', encoding='utf-8')
sys.stdout = output_file
sys.stderr = output_file

print("\n" + "="*60)
print("TESTING INDIVIDUAL SCRAPERS")
print("="*60 + "\n")

# Test Reddit
print("[1/3] Testing Reddit Scraper...")
print("="*60)
try:
    sys.path.append('.')
    from scrapers import scrape_reddit
    reddit_problems = scrape_reddit(limit=3)
    print(f"✅ Reddit returned {len(reddit_problems)} problems")
    if reddit_problems:
        print(f"Sample: {reddit_problems[0]['title'][:60]}...")
except Exception as e:
    print(f"❌ Reddit scraper failed: {e}")

print()

# Test Stack Overflow
print("[2/3] Testing Stack Overflow Scraper...")
print("="*60)
try:
    from scrapers import scrape_stackoverflow
    so_problems = scrape_stackoverflow(limit=3)
    print(f"✅ Stack Overflow returned {len(so_problems)} problems")
    if so_problems:
        print(f"Sample: {so_problems[0]['title'][:60]}...")
except Exception as e:
    print(f"❌ Stack Overflow scraper failed: {e}")

print()

# Test Hacker News
print("[3/3] Testing Hacker News Scraper...")
print("="*60)
try:
    from scrapers import scrape_hackernews
    hn_problems = scrape_hackernews(limit=3)
    print(f"✅ Hacker News returned {len(hn_problems)} problems")
    if hn_problems:
        print(f"Sample: {hn_problems[0]['title'][:60]}...")
        print(f"\nChecking new fields on first problem:")
        first = hn_problems[0]
        print(f"  - source_id: {first.get('source_id', 'MISSING')}")
        print(f"  - humanized_explanation: {first.get('humanized_explanation', 'MISSING')[:50] if first.get('humanized_explanation') else 'MISSING'}...")
        print(f"  - solution_possibility: {first.get('solution_possibility', 'MISSING')}")
except Exception as e:
    print(f"❌ Hacker News scraper failed: {e}")

print("\n" + "="*60 + "\n")

output_file.close()
print("Results saved to scraper_test_results.txt", file=sys.__stdout__)


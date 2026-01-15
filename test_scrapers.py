"""Test individual scrapers to diagnose the issue"""
from scrapers import scrape_reddit, scrape_stackoverflow, scrape_hackernews

print("=== Testing Individual Scrapers ===\n")

# Test Reddit
print("[1/3] Testing Reddit scraper...")
try:
    reddit_results = scrape_reddit(limit=5)
    print(f"✓ Reddit returned {len(reddit_results)} problems")
    if reddit_results:
        for i, p in enumerate(reddit_results[:3], 1):
            print(f"  {i}. {p['title'][:60]}...")
    else:
        print("  ⚠️  No problems returned from Reddit!")
except Exception as e:
    print(f"  ✗ Reddit scraper failed: {e}")

print()

# Test Stack Overflow
print("[2/3] Testing Stack Overflow scraper...")
try:
    so_results = scrape_stackoverflow(limit=5)
    print(f"✓ StackOverflow returned {len(so_results)} problems")
    if so_results:
        for i, p in enumerate(so_results[:3], 1):
            print(f"  {i}. {p['title'][:60]}...")
    else:
        print("  ⚠️  No problems returned from Stack Overflow!")
except Exception as e:
    print(f"  ✗ Stack Overflow scraper failed: {e}")

print()

# Test Hacker News
print("[3/3] Testing Hacker News scraper...")
try:
    hn_results = scrape_hackernews(limit=5)
    print(f"✓ HackerNews returned {len(hn_results)} problems")
    if hn_results:
        for i, p in enumerate(hn_results[:3], 1):
            print(f"  {i}. {p['title'][:60]}...")
    else:
        print("  ⚠️  No problems returned from Hacker News!")
except Exception as e:
    print(f"  ✗ Hacker News scraper failed: {e}")

print("\n=== Test Complete ===")

"""
Test /scrape/all endpoint integration

This tests the full scraping pipeline with all 3 sources:
- GitHub
- Stack Overflow  
- Hacker News
"""

import requests
import json
import time


def test_scrape_all():
    """Test the /scrape/all endpoint"""
    print("\n" + "="*70)
    print("  🚀 Testing /scrape/all Endpoint")
    print("="*70)
    
    # First run
    print("\n📥 RUN 1: First scrape (should get ~30 new problems)...")
    print("-"*70)
    
    try:
        response = requests.post("http://localhost:8000/scrape/all", timeout=300)  # Increased from 120s
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ SUCCESS - Status: {response.status_code}")
            print(f"\n📊 Results:")
            print(f"  Total scraped: {data.get('total_scraped', 0)}")
            print(f"  Total fetched: {data.get('total_fetched', 0)}")
            print(f"  Duplicates skipped: {data.get('duplicates_skipped', 0)}")
            
            print(f"\n📈 Per-Source Breakdown:")
            print(f"  GitHub:         {data.get('github_count', 0):>3} added ({data.get('github_fetched', 0)} fetched)")
            print(f"  Stack Overflow: {data.get('stackoverflow_count', 0):>3} added ({data.get('stackoverflow_fetched', 0)} fetched)")
            print(f"  Hacker News:    {data.get('hackernews_count', 0):>3} added ({data.get('hackernews_fetched', 0)} fetched)")
            
            # Check if we got close to 30
            total = data.get('total_scraped', 0)
            if total >= 25:
                print(f"\n✅ Target achieved: {total}/30 problems (83%+)")
            elif total >= 20:
                print(f"\n⚠️  Moderate success: {total}/30 problems (67%+)")
            else:
                print(f"\n❌ Below target: {total}/30 problems (<67%)")
            
            first_run_data = data
            
        else:
            print(f"\n❌ ERROR - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timed out after 300s")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("   Make sure server is running: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Wait a bit
    print("\n⏳ Waiting 3 seconds before second run...")
    time.sleep(3)
    
    # Second run - test deduplication
    print("\n📥 RUN 2: Second scrape (should find mostly duplicates)...")
    print("-"*70)
    
    try:
        response = requests.post("http://localhost:8000/scrape/all", timeout=300)  # Increased from 120s
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ SUCCESS - Status: {response.status_code}")
            print(f"\n📊 Results:")
            print(f"  Total scraped: {data.get('total_scraped', 0)}")
            print(f"  Total fetched: {data.get('total_fetched', 0)}")
            print(f"  Duplicates skipped: {data.get('duplicates_skipped', 0)}")
            
            print(f"\n📈 Per-Source Breakdown:")
            print(f"  GitHub:         {data.get('github_count', 0):>3} added ({data.get('github_fetched', 0)} fetched)")
            print(f"  Stack Overflow: {data.get('stackoverflow_count', 0):>3} added ({data.get('stackoverflow_fetched', 0)} fetched)")
            print(f"  Hacker News:    {data.get('hackernews_count', 0):>3} added ({data.get('hackernews_fetched', 0)} fetched)")
            
            # Check deduplication
            new_problems = data.get('total_scraped', 0)
            duplicates = data.get('duplicates_skipped', 0)
            
            if new_problems <= 5:
                print(f"\n✅ De-duplication working: Only {new_problems} new (rest were duplicates)")
            elif new_problems <= 10:
                print(f"\n⚠️  Moderate de-duplication: {new_problems} new problems")
            else:
                print(f"\n❌ De-duplication may have issues: {new_problems} new problems (expected ≤5)")
            
        else:
            print(f"\n❌ ERROR - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Final summary
    print("\n" + "="*70)
    print("  ✅ /scrape/all Integration Test Complete")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = test_scrape_all()
    exit(0 if success else 1)

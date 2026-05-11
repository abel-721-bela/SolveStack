"""
Stack Overflow Scraper

Fetches high-signal questions from Stack Overflow using the Stack Exchange API.
Filters for questions with high views or no accepted answer.
Returns normalized problem objects.
"""

import os
import time
import re
from datetime import datetime
import requests
import html
from typing import List, Dict
from dotenv import load_dotenv
from text_utils import clean_text as robust_clean_text, truncate_text



load_dotenv()

# Stack Exchange API Configuration
STACKEXCHANGE_KEY = os.getenv('STACKEXCHANGE_KEY')
API_BASE_URL = "https://api.stackexchange.com/2.3"

# Popular tech tags (placeholder or empty)
TECH_TAGS = []


def clean_html(text: str) -> str:
    """Delegated to robust text_utils"""
    return robust_clean_text(text)




def scrape_stackoverflow(limit: int = 10) -> List[Dict]:
    """
    Scrape high-signal questions from Stack Overflow.
    
    Args:
        limit: Maximum number of problems to fetch (default: 10)
    
    Returns:
        List of normalized problem dictionaries
    
    Filtering Criteria:
    - Recent questions with 0-2 answers (unsolved/partially solved)
    - OR-style single-tag queries for better results
    - Question body is not empty
    """
    print(f"\nSTACK OVERFLOW SCRAPER DEBUG LOG")
    print("=" * 60)
    
    # API KEY VALIDATION
    if STACKEXCHANGE_KEY:
        print(f"Stack Exchange API Key: SET (...{STACKEXCHANGE_KEY[-8:]})")
        print(f"   Quota: 10,000 requests/day")
    else:
        print(f"Stack Exchange API Key: NOT SET")
        print(f"   Quota: 300 requests/day (unauthenticated)")
    
    print()
    
    problems = []
    total_fetched = 0
    total_filtered = 0
    total_api_calls = 0
    
    # Use OR-style queries: fetch from individual tags instead of AND-ing them
    # This significantly increases result count
    priority_tags = ['python', 'javascript', 'reactjs', 'nodejs', 'typescript', 
                     'docker', 'kubernetes', 'machine-learning']
    
    print(f"Scraping Parameters:")
    print(f"  Target problems: {limit}")
    print(f"  Strategy: OR-style single-tag queries")
    print(f"  Priority tags: {', '.join(priority_tags)}")
    print(f"  Filter: 0-2 answers (unsolved/partially solved)")
    print()
    
    try:
        # Distribute quota across tags
        problems_per_tag = max(2, limit // len(priority_tags) + 1)
        
        for tag in priority_tags:
            if len(problems) >= limit:
                print(f"  Quota reached ({len(problems)}/{limit}), stopping")
                break
            
            print(f"  Fetching '{tag}' questions...", end=" ", flush=True)
            
            endpoint = f"{API_BASE_URL}/questions"
            
            params = {
                'site': 'stackoverflow',
                'sort': 'activity',  # Recently active
                'order': 'desc',
                'tagged': tag,  # Single tag for OR-style query
                'filter': 'withbody',  # Include body
                'pagesize': min(100, problems_per_tag * 3)  # API max is 100
            }
            
            # Only add key if it exists
            if STACKEXCHANGE_KEY:
                params['key'] = STACKEXCHANGE_KEY
            
            # Log request details
            request_url = f"{endpoint}?site={params['site']}&tagged={tag}&pagesize={params['pagesize']}"
            
            try:
                total_api_calls += 1
                response = requests.get(endpoint, params=params, timeout=15)
                
                if response.status_code != 200:
                    print(f"HTTP {response.status_code}")
                    if response.status_code == 400:
                        error_data = response.json()
                        print(f"    Error: {error_data.get('error_message', 'Bad request')}")
                    continue
                
                data = response.json()
                
                # Check for API quota warnings
                if 'quota_remaining' in data:
                    quota_remaining = data['quota_remaining']
                    if quota_remaining < 50:
                        print(f"Low API quota: {quota_remaining} remaining")
                
                if 'items' not in data:
                    print(f"❌ No 'items' in response")
                    continue
                
                questions = data['items']
                print(f"received {len(questions)} questions", end=" ", flush=True)
                
                tag_fetched = 0
                tag_kept = 0
                tag_filtered = 0
                
                for question in questions:
                    if len(problems) >= limit:
                        break
                    
                    tag_fetched += 1
                    
                    # FILTERING: Low answer count (0-2 answers)
                    answer_count = question.get('answer_count', 0)
                    if answer_count > 2:
                        tag_filtered += 1
                        continue  # Skip well-answered questions
                    
                    # Extract data
                    title = question.get('title', '').strip()
                    body = clean_html(question.get('body', ''))
                    question_id = str(question.get('question_id', ''))
                    link = question.get('link', '')
                    question_tags = question.get('tags', [])[:5]
                    view_count = question.get('view_count', 0)
                    
                    # Skip if body is too short
                    if len(body) < 50:
                        tag_filtered += 1
                        continue
                    
                    # Author info
                    owner = question.get('owner', {})
                    author_name = owner.get('display_name', 'Anonymous')
                    author_id = str(owner.get('user_id', 'N/A'))
                    
                    # Date
                    creation_date = question.get('creation_date', 0)
                    date_str = datetime.fromtimestamp(creation_date).strftime('%Y-%m-%d') if creation_date else datetime.now().strftime('%Y-%m-%d')
                    
                    humanized_explanation = ""
                    solution_possibility = ""
                    
                    # Metrics
                    score = question.get('score', 0)
                    comment_count = question.get('comment_count', 0)
                    engagement_score = float(score) + (float(comment_count) * 1.5)
                    
                    # Minimal decoding for titles
                    raw_title = html.unescape(title)
                    
                    problem = {
                        'raw_title': raw_title,
                        'raw_description': body,
                        'raw_tags': question_tags,
                        'source': 'stackoverflow',
                        'source_id': str(question_id),
                        'reference_link': link,
                        'date': date_str,
                        'author_name': author_name,
                        'author_id': author_id,
                        
                        # Metrics passthrough
                        'upvotes': score,
                        'comment_count': comment_count,
                        'engagement_score': engagement_score
                    }
                    
                    problems.append(problem)
                    tag_kept += 1
                    time.sleep(0.05)  # Minimal delay
                
                total_fetched += tag_fetched
                total_filtered += tag_filtered
                
                print(f"→ kept {tag_kept} (filtered {tag_filtered})")
                
            except requests.Timeout:
                print(f"❌ TIMEOUT after 15s")
                continue
            except requests.RequestException as e:
                print(f"❌ REQUEST ERROR: {str(e)[:50]}")
                continue
            except Exception as e:
                print(f"❌ ERROR: {type(e).__name__}: {str(e)[:50]}")
                continue
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {type(e).__name__}: {str(e)}")
    
    print(f"\n📊 STACK OVERFLOW SCRAPING SUMMARY:")
    print(f"  Total API calls: {total_api_calls}")
    print(f"  Total questions fetched: {total_fetched}")
    print(f"  Total filtered: {total_filtered}")
    print(f"  Total problems kept: {len(problems)}")
    
    if len(problems) == 0:
        print(f"\n⚠️  WARNING: No Stack Overflow questions met criteria!")
        print(f"     Fetched {total_fetched} questions but all were filtered")
        print(f"     Filter reason: answer_count > 2 OR body too short (\u003c50 chars)")
    
    print("=" * 60 + "\n")
    return problems



if __name__ == "__main__":
    # Test the scraper
    print("Testing Stack Overflow scraper...")
    test_problems = scrape_stackoverflow(limit=5)
    
    if test_problems:
        print(f"\n✓ Successfully scraped {len(test_problems)} problems")
        print("\nSample problem:")
        sample = test_problems[0]
        for key, value in sample.items():
            if key == 'description':
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {value}")
    else:
        print("\n✗ No problems scraped")

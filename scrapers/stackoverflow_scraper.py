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
from typing import List, Dict
import requests
from dotenv import load_dotenv

load_dotenv()

# Stack Exchange API Configuration
STACKEXCHANGE_KEY = os.getenv('STACKEXCHANGE_KEY')
API_BASE_URL = "https://api.stackexchange.com/2.3"

# Popular tech tags to focus on
TECH_TAGS = [
    'python', 'javascript', 'reactjs', 'java', 'machine-learning', 
    'cloud', 'docker', 'kubernetes', 'nodejs', 'typescript',
    'aws', 'azure', 'gcp', 'django', 'flask', 'spring-boot',
    'postgresql', 'mongodb', 'redis', 'angular', 'vue.js'
]


def clean_html(text: str) -> str:
    """Remove HTML tags and clean text"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def generate_humanized_explanation(title: str, body: str) -> str:
    """
    Generate a simple, human-readable explanation of the problem.
    Extracts first 2-3 sentences or creates a shortened version.
    """
    # Combine title and body
    full_text = f"{title}. {body}"
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', full_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Take first 2-3 sentences, max 250 chars
    explanation = '. '.join(sentences[:3])
    
    if len(explanation) > 250:
        explanation = explanation[:247] + '...'
    
    return explanation


def determine_solution_type(text: str) -> str:
    """
    Determine if the problem requires software, hardware, or hybrid solution.
    
    For Stack Overflow, most problems are software-related.
    """
    text_lower = text.lower()
    
    # Hardware keywords
    hardware_keywords = ['arduino', 'raspberry pi', 'sensor', 'iot device', 'embedded', 'circuit']
    has_hardware = any(kw in text_lower for kw in hardware_keywords)
    
    # Software is default for Stack Overflow
    if has_hardware:
        return 'hybrid'
    
    return 'software'


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
    print(f"\n🔍 STACK OVERFLOW SCRAPER DEBUG LOG")
    print("=" * 60)
    
    # API KEY VALIDATION
    if STACKEXCHANGE_KEY:
        print(f"📋 Stack Exchange API Key: ✓ SET (...{STACKEXCHANGE_KEY[-8:]})")
        print(f"   Quota: 10,000 requests/day")
    else:
        print(f"📋 Stack Exchange API Key: ✗ NOT SET")
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
    
    print(f"📊 Scraping Parameters:")
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
                print(f"  ⏭️  Quota reached ({len(problems)}/{limit}), stopping")
                break
            
            print(f"  📡 Fetching '{tag}' questions...", end=" ", flush=True)
            
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
                    print(f"❌ HTTP {response.status_code}")
                    if response.status_code == 400:
                        error_data = response.json()
                        print(f"    Error: {error_data.get('error_message', 'Bad request')}")
                    continue
                
                data = response.json()
                
                # Check for API quota warnings
                if 'quota_remaining' in data:
                    quota_remaining = data['quota_remaining']
                    if quota_remaining < 50:
                        print(f"⚠️  Low API quota: {quota_remaining} remaining")
                
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
                    
                    # Generate additional fields
                    suggested_tech = ', '.join(question_tags) if question_tags else tag
                    humanized_explanation = generate_humanized_explanation(title, body)
                    solution_possibility = determine_solution_type(f"{title} {body}")
                    
                    problem = {
                        'title': title,
                        'description': body[:1000],  # Limit description length
                        'source': 'stackoverflow',
                        'source_id': question_id,
                        'reference_link': link,
                        'tags': question_tags,
                        'suggested_tech': suggested_tech,
                        'humanized_explanation': humanized_explanation,
                        'solution_possibility': solution_possibility,
                        'date': date_str,
                        'author_name': author_name,
                        'author_id': author_id
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

"""
Reddit Scraper (Refactored from pyproblem_shelf.py)

Fetches tech problems from relevant subreddits using PRAW.
Reuses existing filtering and classification logic.
Returns normalized problem objects.
"""

import os
import time
import re
from datetime import datetime
from typing import List, Dict
import praw
from dotenv import load_dotenv

# Import existing helper functions from pyproblem_shelf
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pyproblem_shelf import (
    is_tech_solvable, 
    suggest_tech, 
    clean_text,
    SUBREDDITS
)

load_dotenv()

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')


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
    """
    text_lower = text.lower()
    
    # Hardware keywords
    hardware_keywords = [
        'arduino', 'raspberry pi', 'sensor', 'iot device', 'embedded', 
        'circuit', 'hardware', 'physical device', 'microcontroller'
    ]
    has_hardware = any(kw in text_lower for kw in hardware_keywords)
    
    # Software keywords (strong indicators)
    software_keywords = [
        'app', 'website', 'api', 'code', 'script', 'software',
        'web app', 'mobile app', 'database', 'cloud', 'server'
    ]
    has_software = any(kw in text_lower for kw in software_keywords)
    
    if has_hardware and has_software:
        return 'hybrid'
    elif has_hardware:
        return 'hardware'
    else:
        return 'software'  # Default for Reddit tech posts


def scrape_reddit(limit: int = 10) -> List[Dict]:
    """
    Scrape tech problems from Reddit using PRAW.
    
    Args:
        limit: Maximum number of problems to fetch (default: 10)
    
    Returns:
        List of normalized problem dictionaries
    
    This function reuses the existing is_tech_solvable() filter and
    ML-based tech suggestion from pyproblem_shelf.py
    """
    print(f"\n🔍 REDDIT SCRAPER DEBUG LOG")
    print("=" * 60)
    
    # EXPLICIT CREDENTIAL VALIDATION
    print(f"📋 Checking Reddit credentials...")
    print(f"  REDDIT_CLIENT_ID: {'✓ SET' if REDDIT_CLIENT_ID else '✗ MISSING'} ({'...' + REDDIT_CLIENT_ID[-8:] if REDDIT_CLIENT_ID else 'None'})")
    print(f"  REDDIT_CLIENT_SECRET: {'✓ SET' if REDDIT_CLIENT_SECRET else '✗ MISSING'} ({'...' + REDDIT_CLIENT_SECRET[-8:] if REDDIT_CLIENT_SECRET else 'None'})")
    print(f"  REDDIT_USER_AGENT: {'✓ SET' if REDDIT_USER_AGENT else '✗ MISSING'} ({REDDIT_USER_AGENT if REDDIT_USER_AGENT else 'None'})")
    
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
        error_msg = "❌ REDDIT CREDENTIALS MISSING! Cannot proceed with Reddit scraping."
        print(f"\n{error_msg}")
        print("  Check your .env file for REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT")
        raise ValueError(error_msg)
    
    print(f"✅ All Reddit credentials present\n")
    
    # INITIALIZE REDDIT CLIENT
    print(f"🔗 Initializing Reddit client...")
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        # TEST AUTHENTICATION
        print(f"🔐 Testing Reddit authentication...")
        try:
            # Try to access user info to verify auth
            user = reddit.user.me()
            print(f"✅ Authenticated as: {user.name if user else 'read-only mode'}")
        except Exception as auth_test_error:
            # Script apps run in read-only mode, this is OK
            print(f"✅ Running in read-only mode (script app) - this is normal")
            
    except Exception as e:
        error_msg = f"❌ REDDIT CLIENT INITIALIZATION FAILED: {str(e)}"
        print(f"\n{error_msg}")
        raise RuntimeError(error_msg)
    
    problems = []
    # Fetch 3x the limit to account for filtering
    posts_per_subreddit = max(5, (limit * 3) // len(SUBREDDITS)) + 2
    
    print(f"\n📊 Scraping Parameters:")
    print(f"  Target problems: {limit}")
    print(f"  Subreddits: {len(SUBREDDITS)} ({', '.join(SUBREDDITS)})")
    print(f"  Posts per subreddit: ~{posts_per_subreddit}")
    print()
    
    total_fetched = 0
    total_filtered = 0
    total_errors = 0
    
    for sub in SUBREDDITS:
        if len(problems) >= limit:
            print(f"  ⏭️  Skipping remaining subreddits (quota reached)")
            break
        
        print(f"  📡 Scraping r/{sub}...", end=" ", flush=True)
        fetched = 0
        filtered = 0
        errors = []
        
        try:
            # Attempt to fetch posts
            subreddit_obj = reddit.subreddit(sub)
            posts_generator = subreddit_obj.new(limit=posts_per_subreddit)
            
            for post in posts_generator:
                if len(problems) >= limit:
                    break
                
                fetched += 1
                
                try:
                    # Use existing tech-solvable filter
                    if is_tech_solvable(post.title, post.selftext):
                        cleaned_title = clean_text(post.title)
                        cleaned_body = clean_text(post.selftext)
                        
                        # Use existing ML-based tech suggestion
                        suggested_tech = suggest_tech(cleaned_title + ' ' + cleaned_body)
                        
                        # Author info
                        author_name = str(post.author) if post.author else 'Anonymous'
                        try:
                            author_id = post.author.id if post.author else 'N/A'
                        except Exception:
                            author_id = 'N/A'
                        
                        # Generate new fields
                        humanized_explanation = generate_humanized_explanation(cleaned_title, cleaned_body)
                        solution_possibility = determine_solution_type(f"{cleaned_title} {cleaned_body}")
                        
                        # Tags
                        tags = [post.link_flair_text] if post.link_flair_text else []
                        
                        problem = {
                            'title': cleaned_title,
                            'description': cleaned_body,
                            'source': f'reddit/{sub}',
                            'source_id': post.id,  # Reddit post ID
                            'date': datetime.fromtimestamp(post.created).strftime('%Y-%m-%d'),
                            'suggested_tech': suggested_tech,
                            'humanized_explanation': humanized_explanation,
                            'solution_possibility': solution_possibility,
                            'author_name': author_name,
                            'author_id': author_id,
                            'reference_link': f"https://reddit.com{post.permalink}",
                            'tags': tags
                        }
                        
                        problems.append(problem)
                    else:
                        filtered += 1
                    
                    time.sleep(0.3)  # Reduced from 0.5 for faster scraping
                    
                except Exception as post_error:
                    errors.append(str(post_error))
                    total_errors += 1
                    continue
            
            print(f"fetched {fetched}, kept {fetched - filtered}, filtered {filtered}")
            if errors:
                print(f"    ⚠️  {len(errors)} post-level errors (first: {errors[0][:50]}...)")
                
        except praw.exceptions.Forbidden as e:
            total_errors += 1
            print(f"❌ FORBIDDEN (403): r/{sub} - {str(e)}")
            print(f"    Possible causes: subreddit is private, banned, or credentials lack access")
            
        except praw.exceptions.NotFound as e:
            total_errors += 1
            print(f"❌ NOT FOUND (404): r/{sub} doesn't exist - {str(e)}")
            
        except praw.exceptions.TooManyRequests as e:
            total_errors += 1
            print(f"❌ RATE LIMIT (429): r/{sub} - {str(e)}")
            print(f"    Reddit API rate limit hit. Wait before retrying.")
            
        except praw.exceptions.RedditAPIException as e:
            total_errors += 1
            print(f"❌ REDDIT API ERROR: r/{sub} - {str(e)}")
            for subexception in e.items:
                print(f"    - {subexception.error_type}: {subexception.message}")
                
        except Exception as e:
            total_errors += 1
            print(f"❌ UNKNOWN ERROR: r/{sub} - {type(e).__name__}: {str(e)}")
            continue
        
        total_fetched += fetched
        total_filtered += filtered
    
    print(f"\n📊 REDDIT SCRAPING SUMMARY:")
    print(f"  Total posts fetched: {total_fetched}")
    print(f"  Total posts filtered: {total_filtered}")
    print(f"  Total problems kept: {len(problems)}")
    print(f"  Total errors: {total_errors}")
    
    if len(problems) == 0 and total_fetched > 0:
        warning_msg = f"⚠️  WARNING: Fetched {total_fetched} posts but ALL were filtered out!"
        print(f"\n{warning_msg}")
        print(f"     This means is_tech_solvable() rejected all posts.")
        print(f"     Consider relaxing filter criteria in is_tech_solvable()")
    elif len(problems) == 0 and total_fetched == 0:
        warning_msg = "⚠️  WARNING: No posts fetched from ANY subreddit!"
        print(f"\n{warning_msg}")
        if total_errors > 0:
            print(f"     Likely cause: Errors accessing subreddits (see above)")
        else:
            print(f"     Possible causes: subreddits have no new posts, or all are private/banned")
    
    print("=" * 60 + "\n")
    return problems



if __name__ == "__main__":
    # Test the scraper
    print("Testing Reddit scraper...")
    test_problems = scrape_reddit(limit=5)
    
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

"""
GitHub Issues Scraper

Fetches real-world tech problems from GitHub repositories using the REST API v3.
Discovers repositories via stars, trending, and topics.
Filters for high-quality, actionable issues across multiple domains.
Returns normalized problem objects.
"""

import os
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

# GitHub API Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
API_BASE_URL = "https://api.github.com"

# Repository Discovery Cache (60 minutes)
_REPO_CACHE = {
    'repos': [],
    'timestamp': None,
    'ttl_seconds': 3600  # 60 minutes
}

# Multi-domain topics for diverse issue coverage
TOPICS = [
    'python', 'javascript', 'typescript', 'react', 'vue', 'nodejs',
    'machine-learning', 'deep-learning', 'ai', 'data-science',
    'cloud', 'aws', 'kubernetes', 'docker', 'devops',
    'systems-programming', 'rust', 'go', 'performance',
    'iot', 'embedded', 'robotics', 'computer-vision'
]

# Language-weighted sampling for diversity
LANGUAGE_WEIGHTS = {
    'Python': 0.25,
    'JavaScript': 0.20,
    'TypeScript': 0.15,
    'Go': 0.10,
    'Rust': 0.08,
    'Java': 0.07,
    'C++': 0.05,
    'C': 0.05,
    'Other': 0.05
}

# Labels that indicate good issues to scrape
GOOD_LABELS = [
    'bug', 'enhancement', 'feature', 'good first issue', 'good-first-issue',
    'help wanted', 'help-wanted', 'beginner-friendly', 'performance',
    'optimization', 'question', 'documentation'
]

# Labels to exclude
BAD_LABELS = ['duplicate', 'wontfix', 'invalid', 'spam', 'closed']

# Patterns to identify awesome/resource lists (AVOID these)
AWESOME_LIST_PATTERNS = [
    'awesome-', '-awesome', 'resources', 'curated', 'collection',
    'list-of', '-list', 'reading-list', 'bookmarks', 'links'
]

# Huge repos to avoid (unless labeled "good first issue")
HUGE_REPOS_BLACKLIST = [
    'torvalds/linux', 'chromium/chromium', 'microsoft/vscode',
    'tensorflow/tensorflow', 'facebook/react'
]

# Repo types to PRIORITIZE (active development projects)
PRIORITY_REPO_TYPES = [
    'framework', 'library', 'tool', 'cli', 'api', 'devtools',
    'cloud', 'infrastructure', 'automation', 'ml-framework',
    'robotics-platform', 'iot-platform'
]


def get_headers() -> dict:
    """Get API headers with authentication if token available"""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SolveStack-GitHub-Scraper/1.0'
    }
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    return headers


def is_awesome_list(repo_name: str, repo_description: str) -> bool:
    """
    Check if a repository is an awesome/resource list.
    These don't have real issues - they're just collections of links.
    """
    name_lower = repo_name.lower()
    desc_lower = (repo_description or '').lower()
    combined = name_lower + ' ' + desc_lower
    
    return any(pattern in combined for pattern in AWESOME_LIST_PATTERNS)


def is_cache_valid() -> bool:
    """Check if repository cache is still valid (within TTL)"""
    if not _REPO_CACHE['timestamp']:
        return False
    
    age_seconds = (datetime.now() - _REPO_CACHE['timestamp']).total_seconds()
    return age_seconds < _REPO_CACHE['ttl_seconds']


def get_cached_repos() -> Optional[List[Dict]]:
    """Get repositories from cache if valid, else None"""
    if is_cache_valid() and _REPO_CACHE['repos']:
        print(f"  💾 Using cached repositories ({len(_REPO_CACHE['repos'])} repos, age: {int((datetime.now() - _REPO_CACHE['timestamp']).total_seconds() / 60)}min)")
        return _REPO_CACHE['repos']
    return None


def cache_repos(repos: List[Dict]) -> None:
    """Cache discovered repositories for 60 minutes"""
    _REPO_CACHE['repos'] = repos
    _REPO_CACHE['timestamp'] = datetime.now()
    print(f"  💾 Cached {len(repos)} repositories (TTL: 60min)")


def apply_language_diversity(repos: List[Dict], target_count: int) -> List[Dict]:
    """
    Apply language-weighted sampling to ensure diversity.
    
    Ensures we don't get 100% Python or 100% JavaScript repos.
    Uses weighted random sampling based on LANGUAGE_WEIGHTS.
    """
    if len(repos) <= target_count:
        return repos
    
    # Group by language
    by_language = {}
    for repo in repos:
        lang = repo.get('language') or 'Other'
        if lang not in by_language:
            by_language[lang] = []
        by_language[lang].append(repo)
    
    # Calculate target per language
    selected = []
    for lang, weight in LANGUAGE_WEIGHTS.items():
        target_for_lang = int(target_count * weight)
        if lang in by_language:
            available = by_language[lang]
            # Take up to target, but not more than available
            to_take = min(target_for_lang, len(available))
            selected.extend(available[:to_take])
    
    # If we didn't hit target, fill with remaining repos
    if len(selected) < target_count:
        remaining_repos = [r for r in repos if r not in selected]
        needed = target_count - len(selected)
        selected.extend(remaining_repos[:needed])
    
    return selected[:target_count]


def handle_rate_limit(response: requests.Response) -> None:
    """Handle GitHub API rate limiting with exponential backoff"""
    if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining == 0:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - time.time(), 0) + 5
            print(f"  ⚠️  Rate limit hit. Sleeping for {int(sleep_time)}s...")
            time.sleep(sleep_time)


def discover_starred_repos(limit: int = 5) -> List[Dict]:
    """
    Discover repositories from authenticated user's starred repos.
    
    Requires GITHUB_TOKEN to be set. Provides personalized, high-quality repos.
    Fallback gracefully if not authenticated.
    """
    if not GITHUB_TOKEN:
        return []
    
    headers = get_headers()
    discovered_repos = []
    
    try:
        # Get user's starred repositories
        url = f"{API_BASE_URL}/user/starred"
        params = {
            'per_page': limit * 2,  # Fetch extra for filtering
            'sort': 'updated',
            'direction': 'desc'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        handle_rate_limit(response)
        
        if response.status_code != 200:
            return []
        
        repos = response.json()
        
        for repo in repos:
            if len(discovered_repos) >= limit:
                break
            
            full_name = repo.get('full_name', '')
            repo_name = repo.get('name', '')
            repo_desc = repo.get('description', '')
            
            # Skip awesome/resource lists
            if is_awesome_list(repo_name, repo_desc):
                continue
            
            # Skip huge blacklisted repos
            if full_name in HUGE_REPOS_BLACKLIST:
                continue
            
            # Only include if has open issues
            if repo.get('open_issues_count', 0) > 0:
                discovered_repos.append({
                    'full_name': full_name,
                    'owner': repo.get('owner', {}).get('login', ''),
                    'name': repo_name,
                    'language': repo.get('language', 'Unknown'),
                    'topics': repo.get('topics', []),
                    'stars': repo.get('stargazers_count', 0),
                    'open_issues': repo.get('open_issues_count', 0),
                    'description': repo_desc
                })
        
        time.sleep(0.3)
        
    except Exception as e:
        print(f"  ⚠️  Could not fetch starred repos: {str(e)[:50]}")
    
    return discovered_repos


def discover_trending_repos(limit: int = 5) -> List[Dict]:
    """
    Discover currently trending repositories.
    
    Uses GitHub search with recent creation/updates and high stars growth.
    """
    headers = get_headers()
    discovered_repos = []
    
    try:
        # Search for recently popular repos
        url = f"{API_BASE_URL}/search/repositories"
        params = {
            'q': f'created:>2024-01-01 stars:>100',
            'sort': 'stars',
            'order': 'desc',
            'per_page': limit * 2
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        handle_rate_limit(response)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        repos = data.get('items', [])
        
        for repo in repos:
            if len(discovered_repos) >= limit:
                break
            
            full_name = repo.get('full_name', '')
            repo_name = repo.get('name', '')
            repo_desc = repo.get('description', '')
            
            # Skip awesome/resource lists
            if is_awesome_list(repo_name, repo_desc):
                continue
            
            # Skip huge blacklisted repos
            if full_name in HUGE_REPOS_BLACKLIST:
                continue
            
            # Only include if has open issues
            if repo.get('open_issues_count', 0) > 0:
                discovered_repos.append({
                    'full_name': full_name,
                    'owner': repo.get('owner', {}).get('login', ''),
                    'name': repo_name,
                    'language': repo.get('language', 'Unknown'),
                    'topics': repo.get('topics', []),
                    'stars': repo.get('stargazers_count', 0),
                    'open_issues': repo.get('open_issues_count', 0),
                    'description': repo_desc
                })
        
        time.sleep(0.3)
        
    except Exception as e:
        print(f"  ⚠️  Could not fetch trending repos: {str(e)[:50]}")
    
    return discovered_repos


def discover_repositories(limit: int = 15) -> List[Dict]:
    """
    Discover high-quality repositories across multiple domains.
    
    Strategy:
    - Check cache first (60min TTL) to avoid rediscovery
    - Search by topics (python, ML, cloud, systems, IoT)
    - Include starred repos (if authenticated)
    - Include trending repos
    - Filter awesome lists (resource collections)
    - Apply language-weighted sampling for diversity
    - Filter by stars (>500 for topics, >100 for trending) and recent activity
    - Ensure language diversity
    
    Returns list of repo objects with owner, name, language, topics
    """
    print(f"\n🔍 Discovering GitHub repositories...")
    
    # CHECK CACHE FIRST
    cached_repos = get_cached_repos()
    if cached_repos:
        # Apply language diversity and return
        return apply_language_diversity(cached_repos, limit)
    
    headers = get_headers()
    discovered_repos = []
    repos_seen = set()
    
    # STRATEGY 1: Starred repos (if authenticated) - up to 20% of limit
    starred_limit = max(2, limit // 5)
    starred_repos = discover_starred_repos(limit=starred_limit)
    if starred_repos:
        print(f"  📌 Found {len(starred_repos)} starred repos")
        for repo in starred_repos:
            if repo['full_name'] not in repos_seen:
                repos_seen.add(repo['full_name'])
                discovered_repos.append(repo)
    
    # STRATEGY 2: Trending repos - up to 20% of limit
    trending_limit = max(2, limit // 5)
    trending_repos = discover_trending_repos(limit=trending_limit)
    if trending_repos:
        print(f"  🔥 Found {len(trending_repos)} trending repos")
        for repo in trending_repos:
            if len(discovered_repos) >= limit:
                break
            if repo['full_name'] not in repos_seen:
                repos_seen.add(repo['full_name'])
                discovered_repos.append(repo)
    
    # STRATEGY 3: Topic-based search - remaining quota
    remaining = limit - len(discovered_repos)
    if remaining > 0:
        topics_to_search = TOPICS[:max(5, remaining // 2)]  # Use subset of topics
        
        for topic in topics_to_search:
            if len(discovered_repos) >= limit:
                break
            
            try:
                # Search for repos by topic, sorted by stars
                url = f"{API_BASE_URL}/search/repositories"
                params = {
                    'q': f'topic:{topic} stars:>500 pushed:>2024-01-01',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 5
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                handle_rate_limit(response)
                
                if response.status_code != 200:
                    print(f"  ⚠️  Failed to search topic '{topic}': HTTP {response.status_code}")
                    continue
                
                data = response.json()
                repos = data.get('items', [])
                
                for repo in repos:
                    if len(discovered_repos) >= limit:
                        break
                    
                    full_name = repo.get('full_name', '')
                    repo_name = repo.get('name', '')
                    repo_desc = repo.get('description', '')
                    
                    # Skip if already seen
                    if full_name in repos_seen:
                        continue
                    
                    # Skip awesome/resource lists
                    if is_awesome_list(repo_name, repo_desc):
                        continue
                    
                    # Skip huge blacklisted repos (will allow them later if labeled)
                    if full_name in HUGE_REPOS_BLACKLIST:
                        continue
                    
                    repos_seen.add(full_name)
                    discovered_repos.append({
                        'full_name': full_name,
                        'owner': repo.get('owner', {}).get('login', ''),
                        'name': repo_name,
                        'language': repo.get('language', 'Unknown'),
                        'topics': repo.get('topics', []),
                        'stars': repo.get('stargazers_count', 0),
                        'open_issues': repo.get('open_issues_count', 0),
                        'description': repo_desc
                    })
                
                time.sleep(0.5)  # Respectful rate limiting
                
            except Exception as e:
                print(f"  ❌ Error discovering repos for topic '{topic}': {str(e)[:50]}")
                continue
    
    print(f"  ✅ Discovered {len(discovered_repos)} repositories (starred={len(starred_repos)}, trending={len([r for r in trending_repos if r['full_name'] in repos_seen])}, topics={len(discovered_repos)-len(starred_repos)-len([r for r in trending_repos if r['full_name'] in repos_seen])})")
    
    # CACHE RESULTS FOR 60 MINUTES
    if discovered_repos:
        cache_repos(discovered_repos)
    
    # APPLY LANGUAGE DIVERSITY
    final_repos = apply_language_diversity(discovered_repos, limit)
    return final_repos


def fetch_issues_from_repo(repo: Dict, limit: int = 3) -> List[Dict]:
    """
    Fetch open issues from a specific repository.
    
    STRICTER Filters (v2):
    - Open issues only (no PRs)
    - Has description (>= 80 chars minimum)
    - Good labels (bug, enhancement, etc.) OR comments >= 1
    - Recent activity (< 6 months)
    - Exclude bad labels (duplicate, wontfix, spam)
    """
    headers = get_headers()
    issues = []
    
    try:
        owner = repo['owner']
        name = repo['name']
        
        url = f"{API_BASE_URL}/repos/{owner}/{name}/issues"
        params = {
            'state': 'open',
            'sort': 'comments',  # Prioritize issues with more discussion
            'direction': 'desc',
            'per_page': limit * 3  # Fetch extra to account for filtering
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        handle_rate_limit(response)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        # Filter issues
        six_months_ago = datetime.now() - timedelta(days=180)
        
        for issue in data:
            if len(issues) >= limit:
                break
            
            # Skip pull requests (they have 'pull_request' key)
            if 'pull_request' in issue:
                continue
            
            # STRICT: Must have a body with >= 80 characters
            body = issue.get('body', '')
            if not body or len(body.strip()) < 80:
                continue
            
            # Check labels
            labels = [label.get('name', '').lower() for label in issue.get('labels', [])]
            
            # STRICT: Skip bad labels
            if any(bad in labels for bad in BAD_LABELS):
                continue
            
            # STRICT: Must have at least one good label OR comments >= 1
            has_good_label = any(good in labels for good in GOOD_LABELS)
            comments_count = issue.get('comments', 0)
            
            if not has_good_label and comments_count < 1:
                continue
            
            # Check recency (updated within last 6 months)
            updated_at = datetime.fromisoformat(issue.get('updated_at', '').replace('Z', '+00:00'))
            if updated_at.replace(tzinfo=None) < six_months_ago:
                continue
            
            # This is a good issue!
            issues.append({
                'issue_data': issue,
                'repo_full_name': repo['full_name'],
                'repo_language': repo['language'],
                'repo_topics': repo['topics'],
                'labels': labels
            })
        
        time.sleep(0.3)  # Rate limiting between requests
        
    except Exception as e:
        print(f"  ❌ Error fetching issues from {repo.get('full_name', 'unknown')}: {str(e)[:50]}")
    
    return issues


def classify_difficulty(issue_data: Dict, labels: List[str], description: str) -> str:
    """
    Estimate issue difficulty based on labels, description complexity, and keywords.
    
    - Beginner: good-first-issue, beginner-friendly, help-wanted + simple
    - Intermediate: web/mobile/product issues, standard bugs
    - Advanced: systems, ML, infra, performance, long/complex descriptions
    """
    # Check for beginner labels
    beginner_labels = ['good first issue', 'good-first-issue', 'beginner-friendly', 'beginner', 'easy']
    if any(label in labels for label in beginner_labels):
        return 'beginner'
    
    # Check for advanced indicators
    advanced_keywords = [
        'performance', 'optimization', 'memory leak', 'race condition', 'concurrency',
        'distributed', 'architecture', 'scalability', 'kernel', 'compiler',
        'threading', 'async', 'garbage collection', 'memory management'
    ]
    advanced_labels = ['performance', 'optimization', 'complex', 'advanced', 'difficult']
    
    text_lower = (description + ' ' + ' '.join(labels)).lower()
    
    if any(kw in text_lower for kw in advanced_keywords) or any(label in labels for label in advanced_labels):
        return 'advanced'
    
    # Check description length (very long = advanced)
    if len(description.split()) > 500:
        return 'advanced'
    
    # Default to intermediate
    return 'intermediate'


def classify_solution_type(description: str, repo_topics: List[str]) -> str:
    """
    Determine if problem requires software, hardware, or hybrid solution.
    
    - Software: Default for most GitHub issues
    - Hardware: IoT, embedded, firmware, sensors
    - Hybrid: Robotics, drones, 3D printers, mixed systems
    """
    text_lower = description.lower()
    topics_lower = ' '.join(repo_topics).lower()
    combined = text_lower + ' ' + topics_lower
    
    # Hardware keywords
    hardware_keywords = [
        'arduino', 'raspberry pi', 'sensor', 'embedded', 'firmware',
        'microcontroller', 'circuit', 'hardware', 'fpga', 'esp32', 'esp8266'
    ]
    
    # Hybrid keywords
    hybrid_keywords = [
        'robotics', 'robot', 'drone', '3d print', 'cnc', 'automation',
        'iot device', 'smart home', 'wearable'
    ]
    
    has_hardware = any(kw in combined for kw in hardware_keywords)
    has_hybrid = any(kw in combined for kw in hybrid_keywords)
    
    if has_hybrid:
        return 'hybrid'
    elif has_hardware:
        return 'hardware'
    else:
        return 'software'


def generate_humanized_explanation(title: str, body: str) -> str:
    """
    Generate a simple, human-readable explanation of the issue.
    Extracts first 2-3 sentences or creates a shortened version.
    """
    # Clean the body
    body = re.sub(r'```[\s\S]*?```', '', body)  # Remove code blocks
    body = re.sub(r'`[^`]+`', '', body)  # Remove inline code
    body = re.sub(r'http[s]?://\S+', '', body)  # Remove URLs
    body = re.sub(r'\s+', ' ', body).strip()  # Normalize whitespace
    
    # Combine title and body
    full_text = f"{title}. {body}"
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', full_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # Take first 2-3 sentences, max 250 chars
    explanation = '. '.join(sentences[:3])
    
    if len(explanation) > 250:
        explanation = explanation[:247] + '...'
    
    return explanation if explanation else title


def transform_issue_to_problem(issue_obj: Dict) -> Dict:
    """
    Transform a GitHub issue into SolveStack Problem format.
    """
    issue = issue_obj['issue_data']
    repo_full_name = issue_obj['repo_full_name']
    repo_language = issue_obj['repo_language']
    repo_topics = issue_obj['repo_topics']
    labels = issue_obj['labels']
    
    # Extract data
    title = issue.get('title', '').strip()
    body = issue.get('body', '').strip()
    issue_number = issue.get('number', 0)
    html_url = issue.get('html_url', '')
    
    # RESILIENT: None-safe popularity scoring
    # Handle None types for all metrics, default to 0
    comments_count = issue.get('comments') or 0
    reactions = issue.get('reactions') or {}
    plus_ones = reactions.get('+1') or 0
    heart = reactions.get('heart') or 0
    hooray = reactions.get('hooray') or 0
    eyes = reactions.get('eyes') or 0
    
    # Calculate popularity score with weighted reactions
    # Comments are the strongest signal (2x), then +1 reactions (1.5x), other reactions (1x)
    popularity_score = (
        (comments_count * 2) +
        (plus_ones * 1.5) +
        (heart * 1) +
        (hooray * 1) +
        (eyes * 0.5)
    )
    
    # Author info
    user = issue.get('user', {})
    author_name = user.get('login', 'Anonymous')
    author_id = str(user.get('id', 'N/A'))
    
    # Date
    created_at = issue.get('created_at', '')
    date_str = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d') if created_at else datetime.now().strftime('%Y-%m-%d')
    
    # Generate fields
    suggested_tech = repo_language
    if repo_topics:
        suggested_tech += ', ' + ', '.join(repo_topics[:3])
    
    humanized_explanation = generate_humanized_explanation(title, body)
    difficulty = classify_difficulty(issue, labels, body)
    solution_possibility = classify_solution_type(body, repo_topics)
    
    # Limit description length
    description = body[:1000] if len(body) > 1000 else body
    
    # Popularity score (not in Problem model, but useful for logging)
    popularity_score = comments_count + (plus_ones * 2)
    
    return {
        'title': title,
        'description': description,
        'source': f'github/{repo_full_name}',
        'source_id': str(issue_number),
        'date': date_str,
        'suggested_tech': suggested_tech,
        'humanized_explanation': humanized_explanation,
        'solution_possibility': solution_possibility,
        'difficulty': difficulty,
        'author_name': author_name,
        'author_id': author_id,
        'reference_link': html_url,
        'tags': [label.replace(' ', '-') for label in labels],  # Normalize label names
        '_popularity_score': popularity_score  # For internal use (not stored in DB)
    }


def scrape_github(limit: int = 10) -> List[Dict]:
    """
    Scrape tech problems from GitHub Issues using REST API v3.
    
    Args:
        limit: Maximum number of problems to fetch (default: 10)
    
    Returns:
        List of normalized problem dictionaries
    
    Strategy:
    1. Discover repositories across topics (python, ML, cloud, systems, IoT)
    2. Fetch open issues with good labels and activity
    3. Filter for quality (has description, comments, recent activity)
    4. Transform to Problem format with difficulty/solution classification
    """
    print(f"\n🔍 GITHUB ISSUES SCRAPER DEBUG LOG")
    print("=" * 60)
    
    # AUTHENTICATION CHECK
    print(f"📋 Checking GitHub credentials...")
    if GITHUB_TOKEN:
        print(f"  GITHUB_TOKEN: ✓ SET (...{GITHUB_TOKEN[-8:]})")
        print(f"  Rate Limit: 5000 requests/hour (authenticated)")
    else:
        print(f"  GITHUB_TOKEN: ✗ NOT SET")
        print(f"  Rate Limit: 60 requests/hour (unauthenticated)")
        print(f"  ⚠️  WARNING: Low rate limit may cause issues. Set GITHUB_TOKEN in .env")
    print()
    
    problems = []
    total_repos_discovered = 0
    total_issues_fetched = 0
    total_filtered = 0
    
    try:
        # PHASE 1: Discover Repositories
        print(f"📊 Scraping Parameters:")
        print(f"  Target problems: {limit}")
        print(f"  Topics: {', '.join(TOPICS[:8])}...")
        print(f"  Strategy: Multi-domain (web, ML, cloud, systems, IoT)")
        print()
        
        repos = discover_repositories(limit=max(10, limit // 2))
        total_repos_discovered = len(repos)
        
        if not repos:
            print(f"  ❌ No repositories discovered!")
            return []
        
        print(f"\n📦 Discovered Repositories:")
        for i, repo in enumerate(repos[:5], 1):
            print(f"  {i}. {repo['full_name']} ({repo['language']}) - ⭐ {repo['stars']}")
        if len(repos) > 5:
            print(f"  ... and {len(repos) - 5} more")
        
        # PHASE 2: Fetch Issues from Repositories
        print(f"\n📥 Fetching Issues...")
        print("-" * 60)
        
        issues_per_repo = max(2, (limit * 2) // len(repos))  # Fetch 2x for filtering
        
        for repo in repos:
            if len(problems) >= limit:
                print(f"  ⏭️  Quota reached ({len(problems)}/{limit}), stopping")
                break
            
            print(f"  📡 {repo['full_name']}...", end=" ", flush=True)
            
            issues = fetch_issues_from_repo(repo, limit=issues_per_repo)
            total_issues_fetched += len(issues)
            
            if not issues:
                print(f"no qualifying issues")
                continue
            
            print(f"found {len(issues)} issues")
            
            # Transform issues to problems
            for issue_obj in issues:
                if len(problems) >= limit:
                    break
                
                try:
                    problem = transform_issue_to_problem(issue_obj)
                    problems.append(problem)
                except Exception as e:
                    print(f"    ⚠️  Error transforming issue: {str(e)[:50]}")
                    total_filtered += 1
                    continue
        
        # SUMMARY
        print(f"\n📊 GITHUB SCRAPING SUMMARY:")
        print(f"  Repositories discovered: {total_repos_discovered}")
        print(f"  Issues fetched: {total_issues_fetched}")
        print(f"  Problems created: {len(problems)}")
        print(f"  Filtered/errors: {total_filtered}")
        
        # Diversity breakdown
        if problems:
            print(f"\n📈 DIVERSITY BREAKDOWN:")
            
            # By difficulty
            difficulties = {}
            for p in problems:
                diff = p.get('difficulty', 'unknown')
                difficulties[diff] = difficulties.get(diff, 0) + 1
            print(f"  Difficulty: " + ', '.join([f"{k}={v}" for k, v in sorted(difficulties.items())]))
            
            # By solution type
            solution_types = {}
            for p in problems:
                sol_type = p.get('solution_possibility', 'unknown')
                solution_types[sol_type] = solution_types.get(sol_type, 0) + 1
            print(f"  Solution Type: " + ', '.join([f"{k}={v}" for k, v in sorted(solution_types.items())]))
        
        print("=" * 60 + "\n")
        return problems
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {type(e).__name__}: {str(e)}")
        print("=" * 60 + "\n")
        return problems  # Return what we have so far


if __name__ == "__main__":
    # Test the scraper
    print("Testing GitHub Issues scraper...")
    test_problems = scrape_github(limit=5)
    
    if test_problems:
        print(f"\n✓ Successfully scraped {len(test_problems)} problems")
        print("\nSample problem:")
        sample = test_problems[0]
        for key, value in sample.items():
            if key.startswith('_'):  # Skip internal fields
                continue
            if key == 'description':
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {value}")
    else:
        print("\n✗ No problems scraped")

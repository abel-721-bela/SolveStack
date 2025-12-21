import json
import re
import sqlite3
import sys
import time
import os
from datetime import datetime
from dotenv import load_dotenv

import nltk
import pandas as pd
import praw
import torch
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from transformers import pipeline
from github import Github
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Warning: NLTK resources (punkt, stopwords, wordnet) not found. Using basic tokenization as fallback.")
    nltk.download = lambda x: None

# Load environment variables
load_dotenv()

# Reddit API credentials from environment
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')


SUBREDDITS = [
    'techsupport', 'learnprogramming', 'AskEngineers', 'programming', 'MachineLearning',
    'webdev', 'androiddev', 'iosprogramming', 'datascience', 'aws', 'azure', 'javascript',
    'Python', 'java', 'hardware', 'cloudcomputing', 'automation', 'SomebodyMakeThis', 'learnpython', 'productivity', 'Automate'
]


PROBLEM_KEYWORDS = ['how to', 'problem', 'fix', 'build', 'issue', 'help with', 'need solution', 'error', 'bug', 'implement', 'optimize', 'automate', 'script', 'bot', 'daily task', 'repetitive', 'tool', 'app for']
TECH_KEYWORDS = ['app', 'software', 'hardware', 'code', 'web', 'database', 'ai', 'ml', 'python', 'java', 'js', 'api', 'mobile', 'cloud', 'android', 'ios', 'aws', 'azure', 'react', 'node', 'flask', 'django', 'sql', 'mongodb', 'tensorflow', 'sklearn', 'debug', 'error', 'crash', 'performance']


NON_TECH_KEYWORDS = ['feel', 'advice', 'choose', 'learn', 'career', 'job', 'course', 'degree', 'imposter', 'recommendation']


TECH_MAP = {
    'web': ['HTML', 'CSS', 'JS', 'React', 'Node.js', 'Vue', 'Angular'],
    'python': ['Python', 'Flask', 'Django', 'Pandas', 'NumPy'],
    'database': ['SQL', 'MongoDB', 'PostgreSQL', 'MySQL'],
    'ml': ['Machine Learning', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Keras'],
    'ai': ['AI', 'NLP', 'Computer Vision', 'Deep Learning'],
    'java': ['Java', 'Spring', 'Hibernate'],
    'js': ['JavaScript', 'Node.js', 'Express'],
    'mobile': ['Mobile', 'Flutter', 'React Native'],
    'android': ['Android', 'Kotlin'],
    'ios': ['iOS', 'Swift'],
    'cloud': ['Cloud', 'AWS', 'Azure', 'GCP'],
    'hardware': ['Hardware', 'Arduino', 'Raspberry Pi'],
}


device = 0 if torch.cuda.is_available() else -1
zero_shot_classifier = pipeline("zero-shot-classification", device=device)


CANDIDATE_TECH_LABELS = [
    "Python", "Flask", "Django", "SQL", "MongoDB", "HTML", "CSS", "JS", "React", "Node.js",
    "Machine Learning", "AI", "Java", "Android", "iOS", "Cloud", "Hardware"
]

def preprocess_text(text):
    """Advanced NLP preprocessing with fallback."""
    try:
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words('english'))
        tokens = nltk.word_tokenize(text.lower())
        tokens = [lemmatizer.lemmatize(word) for word in tokens if word.isalnum() and word not in stop_words]
    except LookupError:
        
        tokens = [word for word in text.lower().split() if word.isalnum()]
    return ' '.join(tokens)

def is_tech_solvable(title, body):
    """Improved ML classifier: Zero-shot to check if tech-solvable, focused on automation."""
    text = preprocess_text(title + ' ' + body)
    

    has_problem = any(kw in text for kw in PROBLEM_KEYWORDS)
    has_tech = any(kw in text for kw in TECH_KEYWORDS)
    if not (has_problem and has_tech):
        return False
    

    candidate_labels = ["code debugging", "system error", "feature development", "automation task", "general discussion"]
    result = zero_shot_classifier(text, candidate_labels, multi_label=False)
    is_solvable = result['labels'][0] in ["code debugging", "system error", "feature development", "automation task"] and result['scores'][0] > 0.7
    
    
    is_non_tech = any(kw in text for kw in NON_TECH_KEYWORDS)
    return is_solvable and not is_non_tech

def suggest_tech(text):
    """Improved tech suggestion: Zero-shot multi-label classification."""
    processed_text = preprocess_text(text)
    
    
    result = zero_shot_classifier(processed_text, CANDIDATE_TECH_LABELS, multi_label=True)
    
    
    suggested = [label for label, score in zip(result['labels'], result['scores']) if score > 0.5]
    return ', '.join(suggested) or 'General Tech'

def clean_text(text):
    """Data cleaning: Remove URLs, HTML, extras; normalize."""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def scrape_reddit(limit=20):
    """Scrape posts from subreddits with error handling."""
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                        client_secret=REDDIT_CLIENT_SECRET,
                        user_agent=REDDIT_USER_AGENT)

    problems = []
    for sub in SUBREDDITS:
        print(f"Scraping r/{sub}...")
        try:
            for post in reddit.subreddit(sub).new(limit=limit):
                if is_tech_solvable(post.title, post.selftext):
                    cleaned_title = clean_text(post.title)
                    cleaned_body = clean_text(post.selftext)
                    suggested_tech = suggest_tech(cleaned_title + ' ' + cleaned_body)
                    author_name = str(post.author) if post.author else 'Anonymous'
                    try:
                        author_id = post.author.id if post.author else 'N/A'
                    except Exception as e:
                        print(f"Warning: Could not fetch author ID for post '{cleaned_title[:30]}...': {e}")
                        author_id = 'N/A'
                    reference_link = f"https://reddit.com{post.permalink}"
                    tags = [post.link_flair_text] if post.link_flair_text else []
                    problems.append({
                        'title': cleaned_title,
                        'description': cleaned_body,
                        'source': f'reddit/{sub}',
                        'date': datetime.fromtimestamp(post.created).strftime('%Y-%m-%d'),
                        'suggested_tech': suggested_tech,
                        'author_name': author_name,
                        'author_id': author_id,
                        'reference_link': reference_link,
                        'tags': tags
                    })
                time.sleep(0.5)
        except Exception as e:
            print(f"Error scraping r/{sub}: {e}")
            continue
    print(f"Scraped {len(problems)} problem statements.")
    return problems

def scrape_github(limit=20):
    """Scrape GitHub Issues globally with tech-solvable filter"""
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("Warning: GITHUB_TOKEN not found. Using unauthenticated requests (60/hour limit).")
        g = Github()
    else:
        g = Github(github_token)
    
    problems = []
    
    # Global search for issues with relevant keywords
    query = 'is:issue is:open label:bug OR label:enhancement OR label:feature'
    
    try:
        issues = g.search_issues(query=query, sort='created', order='desc')
        
        count = 0
        for issue in issues:
            if count >= limit:
                break
                
            # Apply same tech-solvable filter
            if is_tech_solvable(issue.title, issue.body or ''):
                cleaned_title = clean_text(issue.title)
                cleaned_body = clean_text(issue.body or '')
                suggested_tech = suggest_tech(cleaned_title + ' ' + cleaned_body)
                
                problems.append({
                    'title': cleaned_title,
                    'description': cleaned_body,
                    'source': f'github/{issue.repository.full_name}',
                    'date': issue.created_at.strftime('%Y-%m-%d'),
                    'suggested_tech': suggested_tech,
                    'author_name': issue.user.login if issue.user else 'Anonymous',
                    'author_id': str(issue.user.id) if issue.user else 'N/A',
                    'reference_link': issue.html_url,
                    'tags': [label.name for label in issue.labels[:3]]
                })
                count += 1
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"Scraped {len(problems)} GitHub issues.")
    except Exception as e:
        print(f"Error scraping GitHub: {e}")
    
    return problems

def scrape_all(limit=20):
    """Unified scraper for all platforms"""
    print("Starting multi-platform scrape...")
    
    reddit_problems = scrape_reddit(limit=limit)
    github_problems = scrape_github(limit=limit)
    
    all_problems = reddit_problems + github_problems
    print(f"Total scraped: {len(all_problems)} problems")
    
    return all_problems

def store_problems_in_db(new_problems, db: Session):
    """Store cleaned problems in database using ORM (works with PostgreSQL or SQLite)"""
    from models import Problem
    
    inserted = 0
    for problem_data in new_problems:
        try:
            # Create Problem instance
            new_problem = Problem(
                title=problem_data['title'],
                description=problem_data['description'],
                source=problem_data['source'],
                date=problem_data['date'],
                suggested_tech=problem_data['suggested_tech'],
                author_name=problem_data['author_name'],
                author_id=problem_data['author_id'],
                reference_link=problem_data['reference_link'],
                tags=problem_data['tags']
            )
            
            db.add(new_problem)
            db.commit()
            inserted += 1
        except IntegrityError:
            # Duplicate reference_link
            db.rollback()
            continue
        except Exception as e:
            print(f"Error inserting problem: {e}")
            db.rollback()
            continue
    
    print(f"Added {inserted} new problems to database (duplicates skipped).")
    return inserted

def export_to_json():
    """Export all problems from DB to a JSON file."""
    conn = sqlite3.connect('problems.db')
    df = pd.read_sql_query("SELECT * FROM problem_statements", conn)
    conn.close()
    problems = df.to_dict(orient='records')
    for problem in problems:
        if isinstance(problem['tags'], str):
            problem['tags'] = json.loads(problem['tags']) if problem['tags'] else []
    with open('problems.json', 'w') as f:
        json.dump(problems, f, indent=4, default=str)
    print(f"Exported {len(problems)} problems to problems.json")

def suggest_ps(tech_input):
    """Suggest PS based on user tech stacks."""
    conn = sqlite3.connect('problems.db')
    query = "SELECT * FROM problem_statements WHERE suggested_tech LIKE ?"
    suggestions = pd.read_sql_query(query, conn, params=[f'%{tech_input.lower()}%'])
    conn.close()
    if suggestions.empty:
        print("No matches found. Try broader tech like 'python'.")
    else:
        print("\nSuggested Problem Statements:")
        for _, row in suggestions.iterrows():
            print(f"- PS ID: {row['ps_id']}\n  Title: {row['title']}\n  Desc: {row['description'][:100]}...\n  Tech: {row['suggested_tech']}\n  Author: {row['author_name']} (ID: {row['author_id']})\n  Link: {row['reference_link']}\n  Tags: {row['tags']}\n")

if __name__ == "__main__":
    print("Scraping and processing...")
    scraped_problems = scrape_reddit(limit=20)
    store_in_db(scraped_problems)
    export_to_json()
    
    
    while True:
        tech = input("\nEnter tech stacks (e.g., 'python web') or 'exit': ").strip()
        if tech.lower() == 'exit':
            break
        suggest_ps(tech)
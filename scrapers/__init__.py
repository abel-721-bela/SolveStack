"""
Multi-Source Problem Scraping Module

This package contains scrapers for different platforms:
- Reddit (via PRAW API)
- Stack Overflow (via Stack Exchange API)
- Hacker News (via Official HN Firebase API)

Each scraper returns a normalized list of problem dictionaries.
"""

from .github_scraper import scrape_github
from .stackoverflow_scraper import scrape_stackoverflow
from .hackernews_scraper import scrape_hackernews

__all__ = ['scrape_github', 'scrape_stackoverflow', 'scrape_hackernews']

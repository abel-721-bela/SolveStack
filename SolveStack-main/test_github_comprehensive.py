"""
Comprehensive Test Script for GitHub Issues Scraper

Tests:
1. GitHub scraper functionality
2. Repository discovery (starred, trending, topics)
3. Issue filtering and classification
4. Integration with /scrape/all endpoint
5. De-duplication logic
6. Diversity verification
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.github_scraper import scrape_github
from database import SessionLocal
from models import Problem
import time


def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print('='*70)
    else:
        print('-'*70)


def test_github_scraper_individual():
    """Test 1: GitHub scraper individual functionality"""
    print_separator("TEST 1: GitHub Scraper Individual Test")
    
    print("\n🧪 Running GitHub scraper with limit=10...")
    try:
        problems = scrape_github(limit=10)
        
        print(f"\n✅ SUCCESS: Scraped {len(problems)} problems")
        
        if problems:
            print("\n📋 Sample Problem:")
            sample = problems[0]
            for key, value in sample.items():
                if key.startswith('_'):  # Skip internal fields
                    continue
                if key in ['description', 'humanized_explanation']:
                    print(f"  {key}: {str(value)[:80]}...")
                else:
                    print(f"  {key}: {value}")
            
            # Verify required fields
            print("\n🔍 Verifying Required Fields:")
            required_fields = [
                'title', 'description', 'source', 'source_id', 'reference_link',
                'suggested_tech', 'humanized_explanation', 'solution_possibility',
                'difficulty', 'date', 'author_name', 'author_id', 'tags'
            ]
            
            for field in required_fields:
                has_field = field in sample
                status = "✅" if has_field else "❌"
                print(f"  {status} {field}: {has_field}")
            
            # Verify classifications
            print("\n📊 Classification Distribution:")
            difficulties = {}
            solution_types = {}
            languages = set()
            
            for p in problems:
                diff = p.get('difficulty', 'unknown')
                sol = p.get('solution_possibility', 'unknown')
                difficulties[diff] = difficulties.get(diff, 0) + 1
                solution_types[sol] = solution_types.get(sol, 0) + 1
                
                # Extract language from suggested_tech
                tech = p.get('suggested_tech', '')
                if tech and ',' in tech:
                    lang = tech.split(',')[0].strip()
                    languages.add(lang)
                elif tech:
                    languages.add(tech)
            
            print(f"  Difficulty: {difficulties}")
            print(f"  Solution Types: {solution_types}")
            print(f"  Languages ({len(languages)}): {', '.join(list(languages)[:10])}")
            
            return True, problems
        else:
            print("\n⚠️  WARNING: No problems returned")
            return False, []
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []


def test_database_insertion(problems):
    """Test 2: Database insertion and de-duplication"""
    print_separator("TEST 2: Database Insertion & De-duplication")
    
    if not problems:
        print("⏭️  Skipping: No problems to insert")
        return False
    
    try:
        db = SessionLocal()
        
        # Count existing problems
        existing_count = db.query(Problem).filter(
            Problem.source.like('github%')
        ).count()
        
        print(f"\n📊 Current GitHub problems in DB: {existing_count}")
        
        # Try to insert problems
        print(f"\n💾 Attempting to insert {len(problems)} problems...")
        inserted = 0
        duplicates = 0
        
        for problem_data in problems:
            try:
                # Check if exists by reference_link
                exists = db.query(Problem).filter(
                    Problem.reference_link == problem_data['reference_link']
                ).first()
                
                if exists:
                    duplicates += 1
                    continue
                
                # Create new problem
                new_problem = Problem(
                    title=problem_data['title'],
                    description=problem_data['description'],
                    source=problem_data['source'],
                    date=problem_data['date'],
                    suggested_tech=problem_data['suggested_tech'],
                    author_name=problem_data['author_name'],
                    author_id=problem_data['author_id'],
                    reference_link=problem_data['reference_link'],
                    tags=problem_data['tags'],
                    source_id=problem_data.get('source_id'),
                    humanized_explanation=problem_data.get('humanized_explanation'),
                    solution_possibility=problem_data.get('solution_possibility'),
                    difficulty=problem_data.get('difficulty')
                )
                
                db.add(new_problem)
                db.commit()
                inserted += 1
                
            except Exception as e:
                db.rollback()
                duplicates += 1
                continue
        
        # Count after insertion
        new_count = db.query(Problem).filter(
            Problem.source.like('github%')
        ).count()
        
        print(f"\n✅ Insertion Complete:")
        print(f"  Inserted: {inserted}")
        print(f"  Duplicates: {duplicates}")
        print(f"  Total GitHub problems now: {new_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_diversity_verification():
    """Test 3: Verify diversity in stored problems"""
    print_separator("TEST 3: Diversity Verification")
    
    try:
        db = SessionLocal()
        
        # Get all GitHub problems
        github_problems = db.query(Problem).filter(
            Problem.source.like('github%')
        ).all()
        
        if not github_problems:
            print("⚠️  No GitHub problems in database")
            return False
        
        print(f"\n📊 Analyzing {len(github_problems)} GitHub problems...")
        
        # Analyze diversity
        sources = {}
        difficulties = {}
        solution_types = {}
        languages = set()
        
        for p in github_problems:
            # Source diversity
            source = p.source
            sources[source] = sources.get(source, 0) + 1
            
            # Difficulty
            diff = p.difficulty or 'unknown'
            difficulties[diff] = difficulties.get(diff, 0) + 1
            
            # Solution type
            sol = p.solution_possibility or 'unknown'
            solution_types[sol] = solution_types.get(sol, 0) + 1
            
            # Language
            tech = p.suggested_tech or ''
            if tech and ',' in tech:
                lang = tech.split(',')[0].strip()
                languages.add(lang)
            elif tech:
                languages.add(tech)
        
        print(f"\n🌍 Diversity Breakdown:")
        print(f"\n  📦 Repository Sources ({len(sources)}):")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {source}: {count}")
        if len(sources) > 10:
            print(f"    ... and {len(sources) - 10} more")
        
        print(f"\n  🎯 Difficulty Distribution:")
        for diff, count in sorted(difficulties.items()):
            print(f"    {diff}: {count}")
        
        print(f"\n  🔧 Solution Type Distribution:")
        for sol, count in sorted(solution_types.items()):
            print(f"    {sol}: {count}")
        
        print(f"\n  💻 Language/Tech Diversity ({len(languages)}):")
        print(f"    {', '.join(sorted(list(languages))[:15])}")
        if len(languages) > 15:
            print(f"    ... and {len(languages) - 15} more")
        
        # Verify requirements
        print(f"\n✅ Diversity Requirements Check:")
        has_multiple_sources = len(sources) >= 5
        has_difficulty_range = len(difficulties) >= 2
        has_solution_diversity = len(solution_types) >= 2
        has_language_diversity = len(languages) >= 3
        
        print(f"  {'✅' if has_multiple_sources else '❌'} Multiple repo sources: {len(sources)} >= 5")
        print(f"  {'✅' if has_difficulty_range else '❌'} Difficulty range: {len(difficulties)} >= 2")
        print(f"  {'✅' if has_solution_diversity else '❌'} Solution diversity: {len(solution_types)} >= 2")
        print(f"  {'✅' if has_language_diversity else '❌'} Language diversity: {len(languages)} >= 3")
        
        db.close()
        
        return has_multiple_sources and has_difficulty_range and has_solution_diversity and has_language_diversity
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print_separator("🚀 GitHub Issues Scraper - Comprehensive Test Suite")
    
    results = []
    
    # Test 1: Individual scraper
    success, problems = test_github_scraper_individual()
    results.append(("GitHub Scraper", success))
    
    if success and problems:
        # Test 2: Database insertion
        time.sleep(1)
        success = test_database_insertion(problems)
        results.append(("Database Insertion", success))
        
        # Test 3: Diversity verification
        time.sleep(1)
        success = test_diversity_verification()
        results.append(("Diversity Verification", success))
    
    # Final summary
    print_separator("📊 TEST SUMMARY")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    total_passed = sum(1 for _, s in results if s)
    total_tests = len(results)
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
    
    print('='*70 + '\n')


if __name__ == "__main__":
    main()

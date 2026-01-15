from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv

from models import User, Problem, CollaborationGroup, CollaborationRequest, Base, group_members
from database import engine, get_db
from schemas import (
    UserCreate, UserResponse, Token,
    ProblemResponse, ProblemDetailResponse,
    InterestRequest, InterestResponse,
    CollaborationRequestCreate, CollaborationActionRequest,
    CollaborationRequestResponse, CollaborationStatusResponse, CollaborationGroupInfo,
    ScrapeRequest, ScrapeResponse, ScrapeAllResponse,
    QualityScoreResponse, RecommendationsResponse, CollaborationSuggestionsResponse
)
from auth import (
    create_access_token, get_password_hash, verify_password,
    get_current_user, get_current_premium_user
)
import pyproblem_shelf
from scoring_engine import (
    compute_problem_quality_score,
    compute_match_score,
    compute_compatibility_score
)

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SolveStack API",
    description="Crowdsourced tech problems platform API",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "https://solvestack.vercel.app",  # Production frontend (update with your domain)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Authentication Endpoints ============

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **email**: Valid email address (unique)
    - **username**: Username (3-50 chars, unique)
    - **password**: Password (min 6 chars)
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token, tags=["Authentication"])
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and receive JWT access token
    
    - **username**: Email address (OAuth2 uses 'username' field)
    - **password**: User password
    """
    # Find user by email (OAuth2PasswordRequestForm uses 'username' field for email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse, tags=["Authentication"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information (requires authentication)"""
    return current_user


# ============ Problem Endpoints ============

@app.get("/problems", response_model=List[ProblemResponse], tags=["Problems"])
def get_problems(
    skip: int = 0,
    limit: int = 100,
    tech: str = None,
    source: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all problems with optional filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **tech**: Filter by technology (e.g., 'python', 'react')
    - **source**: Filter by source platform (e.g., 'reddit', 'github')
    """
    query = db.query(Problem)
    
    # Apply filters
    if tech:
        query = query.filter(Problem.suggested_tech.contains(tech))
    if source:
        query = query.filter(Problem.source.contains(source))
    
    problems = query.order_by(Problem.scraped_at.desc()).offset(skip).limit(limit).all()
    
    # Add interested count to each problem
    result = []
    for problem in problems:
        problem_dict = {
            "ps_id": problem.ps_id,
            "title": problem.title,
            "description": problem.description,
            "source": problem.source,
            "date": problem.date,
            "suggested_tech": problem.suggested_tech,
            "author_name": problem.author_name,
            "author_id": problem.author_id,
            "reference_link": problem.reference_link,
            "tags": problem.tags or [],
            "scraped_at": problem.scraped_at,
            "interested_count": len(problem.interested_users)
        }
        result.append(problem_dict)
    
    return result


@app.get("/problems/{problem_id}", response_model=ProblemDetailResponse, tags=["Problems"])
def get_problem_detail(problem_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific problem"""
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    return problem


@app.post("/scrape", response_model=ScrapeResponse, tags=["Admin"])
def trigger_scrape(
    request: ScrapeRequest = ScrapeRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger scraping from configured platforms (admin only)
    
    - **limit**: Number of problems to scrape per platform (default 20)
    - **platforms**: List of platforms to scrape (default: ["reddit", "github"])
    """
    reddit_count = 0
    github_count = 0
    
    try:
        # Scrape based on requested platforms
        if "reddit" in request.platforms:
            reddit_problems = pyproblem_shelf.scrape_reddit(limit=request.limit)
            pyproblem_shelf.store_problems_in_db(reddit_problems, db)
            reddit_count = len(reddit_problems)
        
        if "github" in request.platforms:
            github_problems = pyproblem_shelf.scrape_github(limit=request.limit)
            pyproblem_shelf.store_problems_in_db(github_problems, db)
            github_count = len(github_problems)
        
        total = reddit_count + github_count
        
        return {
            "message": f"Successfully scraped {total} problems",
            "total_scraped": total,
            "reddit_count": reddit_count,
            "github_count": github_count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )


@app.post("/scrape/all", response_model=ScrapeAllResponse, tags=["Admin"])
def scrape_all_sources(db: Session = Depends(get_db)):
    """
    Unified scraper: Fetch problems from all sources (GitHub, Stack Overflow, Hacker News).
    
    Behavior:
    - TARGET: 30 total problems per run
    - Quota redistribution: If one platform returns fewer results, redistributes to others
    - Continues fetching until quota met or all sources exhausted
    - De-duplicates based on:
      1. reference_link (unique constraint)
      2. source + source_id combination
      3. Title similarity within same source (>85% match)
    
    Returns:
        Counts of problems scraped from each source and duplicates skipped
    """
    from scrapers import scrape_github, scrape_stackoverflow, scrape_hackernews
    from sqlalchemy.exc import IntegrityError
    from difflib import SequenceMatcher
    
    def is_similar_title(title1: str, title2: str, threshold: float = 0.85) -> bool:
        """Check if two titles are similar using fuzzy matching"""
        ratio = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        return ratio >= threshold
    
    def is_duplicate(problem_data: dict, db: Session) -> bool:
        """
        Check if problem is a duplicate using multiple strategies.
        Returns True if duplicate, False if unique.
        """
        # Strategy 1: Check reference_link
        existing_link = db.query(Problem).filter(
            Problem.reference_link == problem_data['reference_link']
        ).first()
        
        if existing_link:
            return True
        
        # Strategy 2: Check source + source_id combination
        if problem_data.get('source_id'):
            existing_source_id = db.query(Problem).filter(
                Problem.source == problem_data['source'],
                Problem.source_id == problem_data['source_id']
            ).first()
            
            if existing_source_id:
                return True
        
        # Strategy 3: Check title similarity within same source
        source_prefix = problem_data['source'].split('/')[0]
        similar_problems = db.query(Problem).filter(
            Problem.source.like(f"{source_prefix}%")
        ).order_by(Problem.scraped_at.desc()).limit(500).all()
        
        for existing_problem in similar_problems:
            if is_similar_title(problem_data['title'], existing_problem.title):
                return True
        
        return False
    
    def insert_problems(problems_list: list, db: Session) -> tuple:
        """Insert problems into database, return (inserted_count, duplicates_skipped)"""
        inserted = 0
        duplicates = 0
        
        for problem_data in problems_list:
            if is_duplicate(problem_data, db):
                duplicates += 1
                continue
            
            try:
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
                    solution_possibility=problem_data.get('solution_possibility')
                )
                
                db.add(new_problem)
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()
                duplicates += 1
            except Exception as e:
                print(f"  ❌ Error inserting problem: {e}")
                db.rollback()
        
        return inserted, duplicates
    
    # QUOTA ENFORCEMENT CONSTANTS
    TARGET_TOTAL = 30
    INITIAL_PER_SOURCE = 10
    
    github_count = 0
    stackoverflow_count = 0
    hackernews_count = 0
    total_duplicates = 0
    
    github_fetched = 0
    stackoverflow_fetched = 0
    hackernews_fetched = 0
    
    try:
        print("\n" + "=" * 70)
        print("🚀 MULTI-SOURCE SCRAPING WITH QUOTA ENFORCEMENT")
        print("=" * 70)
        print(f"🎯 TARGET: {TARGET_TOTAL} total problems")
        print(f"📊 STRATEGY: {INITIAL_PER_SOURCE} per source, redistribute if needed")
        print("=" * 70)
        
        # PHASE 1: Initial scraping (10 from each source)
        print(f"\n📥 PHASE 1: Initial Scraping ({INITIAL_PER_SOURCE} per source)")
        print("-" * 70)
        
        # Scrape GitHub
        print(f"\n[1/3] GitHub...")
        try:
            github_problems = scrape_github(limit=INITIAL_PER_SOURCE)
            github_fetched = len(github_problems)
            github_count, github_dups = insert_problems(github_problems, db)
            total_duplicates += github_dups
            print(f"  ✅ GitHub: {github_count} inserted, {github_dups} duplicates")
        except Exception as e:
            print(f"  ❌ GitHub scraping failed: {str(e)[:100]}")
            github_problems = []
        
        # Scrape Stack Overflow
        print(f"\n[2/3] Stack Overflow...")
        try:
            stackoverflow_problems = scrape_stackoverflow(limit=INITIAL_PER_SOURCE)
            stackoverflow_fetched = len(stackoverflow_problems)
            stackoverflow_count, so_dups = insert_problems(stackoverflow_problems, db)
            total_duplicates += so_dups
            print(f"  ✅ Stack Overflow: {stackoverflow_count} inserted, {so_dups} duplicates")
        except Exception as e:
            print(f"  ❌ Stack Overflow scraping failed: {str(e)[:100]}")
            stackoverflow_problems = []
        
        # Scrape Hacker News
        print(f"\n[3/3] Hacker News...")
        try:
            hackernews_problems = scrape_hackernews(limit=INITIAL_PER_SOURCE)
            hackernews_fetched = len(hackernews_problems)
            hackernews_count, hn_dups = insert_problems(hackernews_problems, db)
            total_duplicates += hn_dups
            print(f"  ✅ Hacker News: {hackernews_count} inserted, {hn_dups} duplicates")
        except Exception as e:
            print(f"  ❌ Hacker News scraping failed: {str(e)[:100]}")
            hackernews_problems = []
        
        # Calculate current total
        current_total = github_count + stackoverflow_count + hackernews_count
        
        print(f"\n📊 Phase 1 Complete: {current_total}/{TARGET_TOTAL} problems added")
        
        # PHASE 2: Quota Redistribution (if needed)
        if current_total < TARGET_TOTAL:
            shortage = TARGET_TOTAL - current_total
            print(f"\n📈 PHASE 2: Quota Redistribution")
            print(f"  Shortage: {shortage} problems")
            print(f"  Redistributing to all sources...")
            print("-" * 70)
            
            # Try to fill quota by fetching more from each source
            attempts = 0
            max_attempts = 3  # Prevent infinite loops
            
            while current_total < TARGET_TOTAL and attempts < max_attempts:
                attempts += 1
                additional_per_source = max(5, (shortage // 3) + 1)
                
                print(f"\n  Attempt {attempts}: Fetching {additional_per_source} more from each source...")
                
                # Additional GitHub
                if current_total < TARGET_TOTAL:
                    try:
                        extra_github = scrape_github(limit=additional_per_source)
                        if extra_github:
                            extra_count, extra_dups = insert_problems(extra_github, db)
                            github_count += extra_count
                            github_fetched += len(extra_github)
                            total_duplicates += extra_dups
                            current_total += extra_count
                            print(f"    GitHub: +{extra_count} ({extra_dups} dups)")
                    except:
                        pass
                
                # Additional Stack Overflow
                if current_total < TARGET_TOTAL:
                    try:
                        extra_so = scrape_stackoverflow(limit=additional_per_source)
                        if extra_so:
                            extra_count, extra_dups = insert_problems(extra_so, db)
                            stackoverflow_count += extra_count
                            stackoverflow_fetched += len(extra_so)
                            total_duplicates += extra_dups
                            current_total += extra_count
                            print(f"    Stack Overflow: +{extra_count} ({extra_dups} dups)")
                    except:
                        pass
                
                # Additional Hacker News
                if current_total < TARGET_TOTAL:
                    try:
                        extra_hn = scrape_hackernews(limit=additional_per_source)
                        if extra_hn:
                            extra_count, extra_dups = insert_problems(extra_hn, db)
                            hackernews_count += extra_count
                            hackernews_fetched += len(extra_hn)
                            total_duplicates += extra_dups
                            current_total += extra_count
                            print(f"    Hacker News: +{extra_count} ({extra_dups} dups)")
                    except:
                        pass
                
                shortage = TARGET_TOTAL - current_total
                if shortage <= 0:
                    break
        
        # FINAL SUMMARY
        print(f"\n" + "=" * 70)
        print(f"✅ SCRAPING COMPLETE")
        print("=" * 70)
        print(f"\n📊 TOTALS:")
        print(f"  Problems Added: {current_total}/{TARGET_TOTAL} ({(current_total/TARGET_TOTAL*100):.1f}%)")
        print(f"  Total Fetched: {github_fetched + stackoverflow_fetched + hackernews_fetched}")
        print(f"  Duplicates Skipped: {total_duplicates}")
        
        print(f"\n📈 BY SOURCE:")
        print(f"  GitHub:         {github_count:>3} added ({github_fetched} fetched)")
        print(f"  Stack Overflow: {stackoverflow_count:>3} added ({stackoverflow_fetched} fetched)")
        print(f"  Hacker News:    {hackernews_count:>3} added ({hackernews_fetched} fetched)")
        print("=" * 70 + "\n")
        
        return {
            "message": f"Successfully scraped {current_total} new problems ({total_duplicates} duplicates skipped)",
            "total_scraped": current_total,
            "total_fetched": github_fetched + stackoverflow_fetched + hackernews_fetched,
            "github_count": github_count,
            "github_fetched": github_fetched,
            "stackoverflow_count": stackoverflow_count,
            "stackoverflow_fetched": stackoverflow_fetched,
            "hackernews_count": hackernews_count,
            "hackernews_fetched": hackernews_fetched,
            "duplicates_skipped": total_duplicates,
            "target_per_source": INITIAL_PER_SOURCE,
            "target_total": TARGET_TOTAL
        }
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-source scraping failed: {str(e)}"
        )



# ============ Interest & Collaboration Endpoints ============

@app.post("/interest", response_model=InterestResponse, tags=["Collaboration"])
def mark_interest(
    request: InterestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark interest in a problem (requires authentication)
    
    - **problem_id**: ID of the problem to mark interest in
    """
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == request.problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Check if user already marked interest
    if current_user in problem.interested_users:
        return {
            "message": "Already marked as interested",
            "total_interested": len(problem.interested_users)
        }
    
    # Add interest
    problem.interested_users.append(current_user)
    db.commit()
    
    return {
        "message": "Interest marked successfully",
        "total_interested": len(problem.interested_users)
    }


@app.delete("/interest/{problem_id}", tags=["Collaboration"])
def remove_interest(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove interest from a problem"""
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    if current_user in problem.interested_users:
        problem.interested_users.remove(current_user)
        db.commit()
        return {"message": "Interest removed successfully"}
    
    return {"message": "You were not interested in this problem"}


# ============ Collaboration Endpoints (Phase 2B) ============

# Constant for minimum group size
MIN_GROUP_SIZE = 2

def check_and_create_group(problem_id: int, db: Session):
    """
    Helper function: Check if enough users have accepted and create/update group.
    
    Business Rule: ONE active group per problem with minimum 2 members
    
    Returns: (group_created: bool, group: CollaborationGroup or None)
    
    Future Extensions:
    - Add configurable MIN_GROUP_SIZE per problem
    - Premium users can create instant groups
    - Generate firebase_room_id when group is created (Phase 3)
    """
    # Get all accepted requests for this problem
    accepted_requests = db.query(CollaborationRequest).filter(
        CollaborationRequest.problem_id == problem_id,
        CollaborationRequest.status == 'accepted'
    ).all()
    
    # Check if we have minimum members
    if len(accepted_requests) < MIN_GROUP_SIZE:
        return False, None
    
    # Check if group already exists for this problem (ONE group per problem rule)
    group = db.query(CollaborationGroup).filter(
        CollaborationGroup.problem_id == problem_id
    ).first()
    
    if group:
        # Group exists, add any new members
        existing_member_ids = {member.id for member in group.members}
        new_members = [req.user for req in accepted_requests if req.user_id not in existing_member_ids]
        
        for member in new_members:
            group.members.append(member)
        
        group.is_active = True  # Ensure it's active
        db.commit()
        db.refresh(group)
        return False, group  # Group already existed
    else:
        # Create new group
        group = CollaborationGroup(
            problem_id=problem_id,
            is_active=True
        )
        
        # Add all accepted users as members
        for req in accepted_requests:
            group.members.append(req.user)
        
        db.add(group)
        db.commit()
        db.refresh(group)
        return True, group  # New group created


@app.post("/collaborate/request", response_model=CollaborationRequestResponse, tags=["Collaboration"])
def request_collaboration(
    request: CollaborationRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request to collaborate on a problem.
    
    Business Rules:
    - User must be authenticated
    - User must have marked interest in the problem first
    - One request per user per problem (enforced by unique constraint)
    - Creates request with status='pending'
    
    Future Extensions:
    - Add optional 'message' field for user's pitch/introduction
    - Add expiry date (auto-reject after 7 days)
    - Premium users get priority/instant acceptance
    - Send notification to other interested users
    """
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == request.problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Check if user has marked interest
    if current_user not in problem.interested_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must mark interest in this problem before requesting collaboration"
        )
    
    # Check for existing request (will also be caught by unique constraint)
    existing = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == request.problem_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a collaboration request for this problem (status: {existing.status})"
        )
    
    # Create collaboration request
    collab_request = CollaborationRequest(
        user_id=current_user.id,
        problem_id=request.problem_id,
        status='pending'
    )
    
    db.add(collab_request)
    db.commit()
    db.refresh(collab_request)
    
    return {
        "request_id": collab_request.id,
        "problem_id": collab_request.problem_id,
        "status": collab_request.status,
        "message": "Collaboration request created successfully. Accept it to join the collaboration!",
        "created_at": collab_request.created_at
    }


@app.post("/collaborate/accept", response_model=CollaborationRequestResponse, tags=["Collaboration"])
def accept_collaboration(
    request: CollaborationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept your collaboration request for a problem.
    
    Business Rules:
    - Finds user's pending/accepted request
    - Updates status to 'accepted'
    - If ≥2 users accepted, auto-creates/updates collaboration group
    - ONE group per problem (adds user to existing group if it exists)
    
    Future Extensions:
    - Generate Firebase room ID when group is created
    - Send notifications to all group members
    - Premium users can invite specific collaborators
    - Add group chat initialization
    """
    # Find user's request for this problem
    collab_request = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == request.problem_id
    ).first()
    
    if not collab_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a collaboration request for this problem. Create one first."
        )
    
    # Update status to accepted
    collab_request.status = 'accepted'
    db.commit()
    
    # Check if we should create/update a group
    group_created, group = check_and_create_group(request.problem_id, db)
    
    response_data = {
        "request_id": collab_request.id,
        "problem_id": collab_request.problem_id,
        "status": collab_request.status,
        "created_at": collab_request.created_at,
        "group_created": group_created
    }
    
    if group:
        response_data["group_id"] = group.id
        response_data["total_members"] = len(group.members)
        response_data["collaborators"] = [member.username for member in group.members]
        response_data["message"] = f"Collaboration accepted! You're now in a group with {len(group.members)} members."
    else:
        response_data["message"] = "Collaboration accepted! Waiting for more users to join..."
    
    return response_data


@app.post("/collaborate/reject", response_model=CollaborationRequestResponse, tags=["Collaboration"])
def reject_collaboration(
    request: CollaborationActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject/withdraw your collaboration request.
    
    Business Rules:
    - Updates request status to 'rejected'
    - If user was in a group, removes them
    - If group drops below 2 members, deactivates the group
    - Allows withdrawal even after accepting (accepted → rejected)
    
    Future Extensions:
    - Add 'reason' field for rejection
    - Notify other group members when someone leaves
    - Archive group chat history before deactivation
    """
    # Find user's request
    collab_request = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == request.problem_id
    ).first()
    
    if not collab_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a collaboration request for this problem"
        )
    
    # Update status to rejected
    old_status = collab_request.status
    collab_request.status = 'rejected'
    
    # If user was accepted and possibly in a group, handle group membership
    if old_status == 'accepted':
        group = db.query(CollaborationGroup).filter(
            CollaborationGroup.problem_id == request.problem_id
        ).first()
        
        if group and current_user in group.members:
            # Remove user from group
            group.members.remove(current_user)
            
            # If group now has less than minimum members, deactivate it
            if len(group.members) < MIN_GROUP_SIZE:
                group.is_active = False
    
    db.commit()
    
    return {
        "request_id": collab_request.id,
        "problem_id": collab_request.problem_id,
        "status": collab_request.status,
        "message": "Collaboration request rejected/withdrawn successfully",
        "created_at": collab_request.created_at
    }


@app.get("/collaborate/{problem_id}", response_model=CollaborationStatusResponse, tags=["Collaboration"])
def get_collaboration_status(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get collaboration status for a problem.
    
    Returns:
    - Your request status (if any)
    - Total/pending/accepted request counts
    - Active group information
    - Whether you can request collaboration
    
    Future Extensions:
    - Show pending requests from other users (for group admins)
    - Add 'recommended collaborators' based on skills
    - Show group activity metrics
    - Link to Firebase chat room if group exists
    """
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Get user's request if exists
    user_request = db.query(CollaborationRequest).filter(
        CollaborationRequest.user_id == current_user.id,
        CollaborationRequest.problem_id == problem_id
    ).first()
    
    # Get all requests for this problem
    all_requests = db.query(CollaborationRequest).filter(
        CollaborationRequest.problem_id == problem_id
    ).all()
    
    total_requests = len(all_requests)
    pending_requests = len([r for r in all_requests if r.status == 'pending'])
    accepted_requests = len([r for r in all_requests if r.status == 'accepted'])
    
    # Get active group if exists
    group = db.query(CollaborationGroup).filter(
        CollaborationGroup.problem_id == problem_id,
        CollaborationGroup.is_active == True
    ).first()
    
    # Determine if user can request collaboration
    can_request = current_user in problem.interested_users and user_request is None
    reason = None
    
    if not can_request:
        if current_user not in problem.interested_users:
            reason = "You must mark interest in this problem first"
        elif user_request:
            reason = f"You already have a request (status: {user_request.status})"
    
    # Build response
    response = {
        "problem_id": problem.ps_id,
        "problem_title": problem.title,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "accepted_requests": accepted_requests,
        "can_request": can_request,
        "reason": reason
    }
    
    if user_request:
        response["your_request"] = {
            "request_id": user_request.id,
            "status": user_request.status,
            "created_at": user_request.created_at
        }
    
    if group:
        response["active_group"] = {
            "group_id": group.id,
            "member_count": len(group.members),
            "members": [member.username for member in group.members],
            "created_at": group.created_at,
            "is_active": group.is_active
        }
    
    return response


# ============ Phase 2C: Intelligent Features ============

@app.post("/problems/{problem_id}/score", response_model=QualityScoreResponse, tags=["Phase 2C - Quality Scoring"])
def score_problem_quality(
    problem_id: int,
    db: Session = Depends(get_db)
):
    """
    Compute quality score for a problem using heuristic algorithms.
    
    Scores based on:
    - Description quality (clarity, completeness)
    - Technical depth (complexity, tech stack)
    - Community engagement (interest, upvotes, views)
    - Reproducibility (steps, environment info)
    
    Also classifies difficulty and estimates effort.
    
    **Algorithm is deterministic and fully explainable** - no ML model training.
    
    Future Enhancement:
    - Could batch-score all problems on schedule
    - Auto-update when problem is modified
    - Display scores in frontend UI
    """
    from datetime import datetime
    
    # Find problem
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Compute scores using heuristic algorithm
    result = compute_problem_quality_score(problem)
    
    # Update problem in database
    problem.quality_score = result["quality_score"]
    problem.difficulty = result["difficulty"]
    problem.estimated_effort = result["estimated_effort"]
    problem.score_updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "problem_id": problem.ps_id,
        "quality_score": result["quality_score"],
        "difficulty": result["difficulty"],
        "estimated_effort": result["estimated_effort"],
        "breakdown": result["breakdown"],
        "message": f"Quality score computed: {result['quality_score']}/100 ({result['difficulty']} difficulty)"
    }


@app.get("/recommendations", response_model=RecommendationsResponse, tags=["Phase 2C - Recommendations"])
def get_personalized_recommendations(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized problem recommendations for the current user.
    
    Matches problems based on:
    - User's skills vs problem technologies (0-40 points)
    - Difficulty level vs user experience (0-20 points)
    - User interests vs problem domain (0-20 points)
    - Novelty/exploration factor (0-20 points)
    
    Returns ranked list with match scores and human-readable reasons.
    
    **READ-ONLY**: Does not auto-select or mark interest.
    
    Future Enhancement:
    - Add filtering by difficulty/effort
    - Include "learning path" suggestions
    - Premium users get more recommendations
    """
    # Get all problems
    all_problems = db.query(Problem).all()
    
    if not all_problems:
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "total_recommendations": 0,
            "recommendations": []
        }
    
    # Compute match score for each problem
    recommendations = []
    
    for problem in all_problems:
        match_result = compute_match_score(current_user, problem)
        
        # Only include if match score > 20 (some relevance)
        if match_result["match_score"] > 20:
            recommendations.append({
                "problem_id": problem.ps_id,
                "title": problem.title,
                "suggested_tech": problem.suggested_tech or "",
                "difficulty": problem.difficulty or "Intermediate",
                "estimated_effort": problem.estimated_effort or "1-3 days",
                "quality_score": problem.quality_score or 0,
                "match_score": match_result["match_score"],
                "reasons": match_result["reasons"]
            })
    
    # Sort by match score descending
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Limit results
    top_recommendations = recommendations[:limit]
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "total_recommendations": len(top_recommendations),
        "recommendations": top_recommendations
    }


@app.get("/collaborate/suggestions/{problem_id}", response_model=CollaborationSuggestionsResponse, tags=["Phase 2C - Smart Suggestions"])
def get_collaboration_suggestions(
    problem_id: int,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get smart collaboration suggestions for a problem.
    
    Suggests users who would be good collaborators based on:
    - Skill complementarity (together cover all techs) - 0-35 points
    - Experience balance (mentorship or peer matching) - 0-20 points
    - Activity compatibility (both active) - 0-25 points
    - Past collaboration success - 0-20 points
    
    **READ-ONLY**: Does not auto-send requests or create groups.
    
    **Prerequisite**: Current user must have marked interest in the problem.
    
    Future Enhancement:
    - Add AI-based personality matching
    - Include timezone compatibility
    - Show mutual connections
    - Premium feature: Unlock more suggestions
    """
    # Find problem
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Check if current user has marked interest
    if current_user not in problem.interested_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must mark interest in this problem first to get collaboration suggestions"
        )
    
    # Get all other interested users (exclude current user)
    interested_users = [u for u in problem.interested_users if u.id != current_user.id]
    
    if not interested_users:
        return {
            "problem_id": problem.ps_id,
            "problem_title": problem.title,
            "total_suggestions": 0,
            "suggestions": []
        }
    
    # Compute compatibility score for each candidate
    suggestions = []
    
    for candidate in interested_users:
        compat_result = compute_compatibility_score(current_user, candidate, problem)
        
        suggestions.append({
            "user_id": candidate.id,
            "username": candidate.username,
            "skills": candidate.skills or [],
            "experience_level": candidate.experience_level or "Intermediate",
            "compatibility_score": compat_result["compatibility_score"],
            "reasons": compat_result["reasons"]
        })
    
    # Sort by compatibility score descending
    suggestions.sort(key=lambda x: x["compatibility_score"], reverse=True)
    
    # Limit results
    top_suggestions = suggestions[:limit]
    
    return {
        "problem_id": problem.ps_id,
        "problem_title": problem.title,
        "total_suggestions": len(top_suggestions),
        "suggestions": top_suggestions
    }


# ============ Debug Endpoints ============

@app.get("/db-info", tags=["Debug"])
def get_database_info(db: Session = Depends(get_db)):
    """
    Debug endpoint: Show which database is actually being used.
    
    Returns database URL and type (SQLite vs PostgreSQL).
    Useful for verifying production database connection.
    """
    from sqlalchemy import inspect
    
    # Get database URL (hide password)
    db_url_str = str(engine.url)
    if "@" in db_url_str:
        # Format: postgresql://user:pass@host:port/db
        db_display = db_url_str.split("://")[0] + "://" + db_url_str.split("@")[-1]
    else:
        db_display = db_url_str
    
    # Determine database type
    if "postgresql" in db_url_str:
        db_type = "PostgreSQL"
        status = "🎉 Production Ready!"
    elif "sqlite" in db_url_str:
        db_type = "SQLite"
        status = "⚠️ Development Mode"
    else:
        db_type = "Unknown"
        status = "❓ Unknown Database"
    
    # Count tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    return {
        "database_type": db_type,
        "database_url": db_display,
        "total_tables": len(tables),
        "tables": sorted(tables),
        "status": status
    }


# ============ Health Check ============


@app.get("/", tags=["Health"])
def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "message": "SolveStack API is running",
        "version": "1.0.0"
    }


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

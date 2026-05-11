from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from models import User, Problem, CollaborationGroup, CollaborationRequest, SquadJoinRequest, SquadMessage, Base, group_members
from database import engine, get_db
from schemas import (
    UserCreate, UserResponse, Token,
    ProblemResponse, ProblemDetailResponse,
    InterestRequest, InterestResponse,
    CollaborationRequestCreate, CollaborationActionRequest,
    CollaborationRequestResponse, CollaborationStatusResponse, CollaborationGroupInfo,
    ScrapeRequest, ScrapeResponse, ScrapeAllResponse,
    HybridSearchResponse, SemanticSearchResponse, IntentAwareSearchResponse,
    ShelfResponse, ImpactExplanation, ShelfAnalytics
)
from search_service import get_search_service
from impact_explanation_service import get_explanation_service
from prototype_service import get_prototype_service
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from cleaning_layer import DataCleaner
from engineering_scoring_engine import get_scoring_engine




# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SolveStack API",
    description="Crowdsourced tech problems platform API",
    version="1.0.0"
)

# CORS configuration
# CORS configuration
origins = ["*"]  # Allow all origins for development to fix IP-based access issues

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
    
    - **username**: Email address (OAuth2 uses 'username' field for email)
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
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information (requires authentication)"""
    from models import problem_interests, group_members
    from sqlalchemy import func
    
    # Interested count - Using more robust query
    interested_count = db.query(func.count(problem_interests.c.user_id)).filter(
        problem_interests.c.user_id == current_user.id
    ).scalar() or 0
    
    # Squads count
    squads_count = db.query(func.count(group_members.c.user_id)).filter(
        group_members.c.user_id == current_user.id
    ).scalar() or 0
    
    print(f">>> [PROFILE DEBUG] Request for User ID: {current_user.id} ({current_user.username})")
    print(f">>> [PROFILE DEBUG] Database found - Interests: {interested_count}, Squads: {squads_count}")
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "is_premium": current_user.is_premium,
        "interested_count": interested_count,
        "squads_count": squads_count,
        "skills": current_user.skills or [],
        "interests": current_user.interests or [],
        "activity_score": current_user.activity_score or 0
    }


@app.get("/search/hybrid", response_model=List[HybridSearchResponse], tags=["Search"])
def hybrid_search(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Perform a hybrid search (Semantic + Keyword + Tags)
    
    - **query**: Search string
    - **limit**: Maximum results to return
    """
    search_service = get_search_service()
    
    # We'll just pass the query as query_text. 
    # If the user wants to extract tags, we'd need another layer, 
    # but the request specifically says: query=...
    results = search_service.search(db, query_text=query, limit=limit)
    
    return [
        {
            "ps_id": p.ps_id,
            "title": p.title,
            "description": p.description,
            "semantic_score": p.search_scores["semantic"],
            "keyword_score": p.search_scores["keyword"],
            "tag_score": p.search_scores["tag"],
            "final_score": p.search_scores["final"]
        } for p in results
    ]

@app.get("/search", response_model=IntentAwareSearchResponse, tags=["Search"])
def search(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Perform a Google-style intent-aware search.
    - **query**: Natural language or keyword query
    - **limit**: Maximum results to return
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
        
    search_service = get_search_service()
    
    try:
        results, metadata = search_service.intent_aware_search(
            db, 
            query=query, 
            limit=limit
        )
        
        return {
            "query": query,
            "results": [
                {
                    "ps_id": p.ps_id,
                    "title": p.title,
                    "description": p.description,
                    "tags": p.tags or [],
                    "scores": p.search_scores
                } for p in results
            ],
            "metadata": metadata
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/search/semantic", tags=["Search"])
def semantic_search_endpoint(
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    AI-powered semantic search. Generates a query embedding and computes
    cosine similarity against stored problem embeddings.
    Falls back to keyword search if insufficient embeddings are available.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass

    try:
        import numpy as np
        import json
        from embedding_service import get_embedding_service
        from sqlalchemy import text as sql_text
        from sqlalchemy.orm import defer
        
        embedding_service = get_embedding_service()
        
        # Generate query embedding
        query_embedding = embedding_service.generate_query_embedding(query)
        
        if query_embedding is None:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        
        query_vec = np.array(query_embedding)
        
        # Fetch embeddings via raw SQL to avoid pgvector Vector type issues
        raw_emb_rows = db.execute(sql_text(
            "SELECT ps_id, embedding FROM problems WHERE embedding IS NOT NULL"
        )).fetchall()
        
        # Build ps_id -> embedding map
        embedding_map = {}
        for row in raw_emb_rows:
            ps_id = row[0]
            emb = row[1]
            if emb is not None:
                try:
                    # Handle both string (pgvector) and list (JSON) formats
                    if isinstance(emb, str):
                        emb = json.loads(emb.replace('(', '[').replace(')', ']'))
                    elif isinstance(emb, (list, tuple)):
                        pass  # Already a list
                    else:
                        continue
                    if len(emb) > 0:
                        embedding_map[ps_id] = np.array(emb, dtype=np.float32)
                except:
                    continue
        
        # If we have very few embeddings, fall back to keyword search immediately
        if len(embedding_map) < 10:
            print(f"[SEARCH] Only {len(embedding_map)} embeddings - using keyword fallback")
            from sqlalchemy import or_, func, case, literal
            
            words = [w for w in query.strip().split() if len(w) > 1]  # Skip single-char words
            if not words:
                words = query.strip().split()
            
            conditions = []
            for word in words:
                w = f"%{word}%"
                conditions.extend([
                    Problem.title.ilike(w),
                    Problem.description.ilike(w),
                    Problem.humanized_explanation.ilike(w),
                    Problem.suggested_tech.ilike(w),
                ])
            
            # Load matching problems
            matching = db.query(Problem).options(defer(Problem.embedding)).filter(
                or_(*conditions)
            ).limit(limit * 2).all()  # Fetch extra to allow relevance sorting
            
            # Rank by relevance: count how many fields match each word
            def relevance_score(p):
                score = 0
                title_lower = (p.title or '').lower()
                desc_lower = (p.description or '').lower()
                expl_lower = (p.humanized_explanation or '').lower()
                tech_lower = (p.suggested_tech or '').lower()
                for word in words:
                    wl = word.lower()
                    if wl in title_lower: score += 3  # Title match = strongest
                    if wl in tech_lower: score += 2   # Tech match = strong
                    if wl in expl_lower: score += 1
                    if wl in desc_lower: score += 1
                return score
            
            matching.sort(key=relevance_score, reverse=True)
            problems = matching[:limit]
            
            results = [_map_problem_to_response(p, current_user) for p in problems]
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_type": "keyword_fallback",
                "metadata": {
                    "embeddings_available": len(embedding_map),
                    "fallback_reason": "insufficient_embeddings"
                }
            }
        
        # Compute cosine similarity for all problems with embeddings
        scored_ids = []
        for ps_id, p_vec in embedding_map.items():
            similarity = float(np.dot(query_vec, p_vec))
            scored_ids.append((ps_id, similarity))
        
        # Sort by similarity (highest first)
        scored_ids.sort(key=lambda x: x[1], reverse=True)
        top_ids = scored_ids[:limit]
        
        # --- TAG / KEYWORD BOOST ---
        # Always include problems whose suggested_tech, title, or description
        # contain the search terms (exact substring match, case-insensitive).
        # This ensures searching "java", "python", "android", "ui" etc. always
        # surfaces tag-matched problems, even if their embedding score is low.
        from sqlalchemy import or_ as sql_or
        words = [w for w in query.strip().split() if len(w) > 1] or query.strip().split()
        tag_conditions = []
        for word in words:
            w = f"%{word}%"
            tag_conditions.extend([
                Problem.suggested_tech.ilike(w),
                Problem.title.ilike(w),
                Problem.description.ilike(w),
            ])
        tag_matched = db.query(Problem).options(defer(Problem.embedding)).filter(
            sql_or(*tag_conditions)
        ).limit(limit).all() if tag_conditions else []
        
        # Build score map from semantic results
        semantic_score_map = {ps_id: score for ps_id, score in top_ids}
        
        # Merge: tag-matched problems get a boosted score based on match quality
        def _tag_boost(p):
            tech_l = (p.suggested_tech or '').lower()
            title_l = (p.title or '').lower()
            desc_l = (p.description or '').lower()
            score = 0.0
            for word in words:
                wl = word.lower()
                if wl in tech_l:  score += 0.5   # strongest: tech tag match
                if wl in title_l: score += 0.3   # title match
                if wl in desc_l:  score += 0.1   # description match
            return score
        
        merged: dict[int, tuple] = {}  # ps_id -> (problem_obj, final_score)
        
        # Add all tag-matched problems first
        for p in tag_matched:
            boost = _tag_boost(p)
            sem_score = semantic_score_map.get(p.ps_id, 0.0)
            final_score = max(sem_score, 0.0) + boost
            merged[p.ps_id] = (p, final_score)
        
        # Fetch semantic top results and add any not already in merged
        top_ps_ids = [ps_id for ps_id, _ in top_ids]
        if top_ps_ids:
            problems_list = db.query(Problem).options(defer(Problem.embedding)).filter(
                Problem.ps_id.in_(top_ps_ids)
            ).all()
            for p in problems_list:
                if p.ps_id not in merged:
                    sem_score = semantic_score_map.get(p.ps_id, 0.0)
                    boost = _tag_boost(p)
                    merged[p.ps_id] = (p, sem_score + boost)
        
        # Sort merged results by final score descending
        sorted_merged = sorted(merged.values(), key=lambda x: x[1], reverse=True)
        
        results = []
        for p, final_score in sorted_merged[:limit]:
            r = _map_problem_to_response(p, current_user)
            r["semantic_score"] = round(final_score, 4)
            results.append(r)
        
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "search_type": "semantic",
            "metadata": {
                "embeddings_searched": len(embedding_map),
                "model": "all-MiniLM-L6-v2"
            }
        }
        
    except ImportError as e:
        print(f"[SEARCH] Semantic search unavailable ({e}), falling back to keyword")
        return keyword_search(query=query, limit=limit, db=db, authorization=authorization)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fall back to keyword search on any error
        print(f"[SEARCH] Semantic search error, falling back to keyword: {e}")
        try:
            return keyword_search(query=query, limit=limit, db=db, authorization=authorization)
        except:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/shelf", response_model=ShelfResponse, tags=["Shelf Intelligence"])
def get_shelf(
    mode: str = "explore",
    sort_by: str = "impact",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Access the intelligent Problem Shelf with curated modes.
    - **mode**: explore, production, architecture, high-cognitive
    - **sort_by**: impact, depth, recency
    """
    from sqlalchemy import cast, JSON, func
    query = db.query(Problem)
    
    # Modes
    if mode == "production":
        query = query.filter(Problem.industry_impact_score > 0.6, Problem.signal_quality_score > 0.6)
    elif mode == "architecture":
        query = query.filter(Problem.technical_depth_score > 0.7)
        # Multi-domain: problems with at least 2 tags
        query = query.filter(func.json_array_length(cast(Problem.tags, JSON)) >= 2)
    elif mode == "high-cognitive":
        query = query.filter(Problem.cognitive_complexity_score > 0.7)
    
    # Sorting
    if sort_by == "impact":
        query = query.order_by(Problem.scraped_at.desc())
    elif sort_by == "depth":
        query = query.order_by(Problem.technical_depth_score.desc())
    else:
        # Default to recency if not specified or fallback
        query = query.order_by(Problem.scraped_at.desc())
        
    results = query.limit(limit).all()
    
    return {
        "mode": mode,
        "total_found": len(results),
        "results": [
            {
                "id": p.ps_id,
                "title": p.title,
                "engineering_impact_score": p.engineering_impact_score,
                "technical_depth_score": p.technical_depth_score,
                "industry_impact_score": p.industry_impact_score,
                "cognitive_complexity_score": p.cognitive_complexity_score,
                "signal_quality_score": p.signal_quality_score,
                "tags": p.tags or []
            } for p in results
        ]
    }


@app.get("/shelf/{problem_id}/explain", tags=["Shelf Intelligence"])
def explain_impact(
    problem_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a natural language explanation for why a problem ranks high.
    """
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    explanation_service = get_explanation_service()
    return explanation_service.explain_score(problem)


@app.get("/problems/{problem_id}/prototype", tags=["Shelf Intelligence"])
async def get_problem_prototype(
    problem_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate an AI implementation plan for a problem.
    """
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    prototype_service = get_prototype_service()
    plan = await prototype_service.generate_implementation_plan(problem)
    return {"problem_id": problem_id, "implementation_plan": plan}


@app.get("/analytics/shelf", response_model=ShelfAnalytics, tags=["Shelf Intelligence"])
def get_shelf_analytics(db: Session = Depends(get_db)):
    """
    Global analytics for the Intelligent Shelf.
    """
    from sqlalchemy import func
    total = db.query(Problem).count()
    if total == 0:
        return {
            "total_analyzed": 0, "low_signal_percentage": 0, "avg_impact_score": 0,
            "top_impact_problems": [], "eis_distribution": []
        }
    
    avg_impact = db.query(func.avg(Problem.engineering_impact_score)).scalar()
    low_signal = db.query(Problem).filter(Problem.signal_quality_score < 0.4).count()
    
    top_5 = db.query(Problem).order_by(Problem.scraped_at.desc()).limit(5).all()
    
    # Distribution
    distribution = []
    buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    for start, end in buckets:
        count = db.query(Problem).filter(
            Problem.engineering_impact_score >= start,
            Problem.engineering_impact_score < (end if end < 100 else 101)
        ).count()
        distribution.append({"bucket": f"{start}-{end}", "count": count})
        
    return {
        "total_analyzed": total,
        "low_signal_percentage": round((low_signal / total) * 100, 2),
        "avg_impact_score": round(avg_impact or 0, 2),
        "top_impact_problems": [
            {"id": p.ps_id, "title": p.title, "score": p.engineering_impact_score}
            for p in top_5
        ],
        "eis_distribution": distribution
    }


# ============ Admin: Regenerate Humanized Explanations ============

@app.post("/admin/regenerate-explanations", tags=["Admin"])
def regenerate_explanations(
    limit: int = 0,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """
    Batch-regenerate humanized explanations for all problems using AI.
    
    - **limit**: Max problems to process (0 = all)
    - **force**: If True, regenerate even for problems that already have explanations
    
    Uses Gemini API first, falls back to Groq, then heuristic.
    Also deep-cleans titles to remove HTML entities and artifacts.
    """
    from humanize_service import humanize_problem
    from text_utils import deep_clean_title, deep_clean_description
    import time
    
    # Fetch problems that need processing
    query = db.query(Problem)
    if not force:
        # Only problems with empty/null/bad/incomplete explanations
        from sqlalchemy import or_, and_, not_, func
        query = query.filter(
            or_(
                Problem.humanized_explanation == None,
                Problem.humanized_explanation == "",
                Problem.humanized_explanation == Problem.title,
                # Catch ones with code snippets
                Problem.humanized_explanation.contains("[code snippet]"),
                Problem.humanized_explanation.contains("```"),
                # Catch incomplete (doesn't end with . ! or ?)
                and_(
                    Problem.humanized_explanation != None,
                    Problem.humanized_explanation != "",
                    not_(Problem.humanized_explanation.op('~')(r'[.!?]["\']?\s*$'))
                )
            )
        )
    
    problems = query.all()
    if limit > 0:
        problems = problems[:limit]
    
    total = len(problems)
    updated = 0
    errors = 0
    providers = {"gemini": 0, "groq": 0, "heuristic": 0}
    titles_cleaned = 0
    
    print(f"\n{'='*60}")
    print(f"REGENERATING HUMANIZED EXPLANATIONS")
    print(f"Total problems to process: {total}")
    print(f"Force mode: {force}")
    print(f"{'='*60}\n")
    
    for i, problem in enumerate(problems, 1):
        try:
            # 1. Deep-clean the title
            old_title = problem.title or ""
            new_title = deep_clean_title(old_title)
            if new_title != old_title:
                problem.title = new_title
                titles_cleaned += 1
            
            # 2. Deep-clean the description
            if problem.description:
                problem.description = deep_clean_description(problem.description)
            
            # 3. Generate humanized explanation
            explanation, provider = humanize_problem(
                problem.title or "",
                problem.description or ""
            )
            
            if explanation:
                problem.humanized_explanation = explanation
                providers[provider] = providers.get(provider, 0) + 1
                updated += 1
                print(f"  [{i}/{total}] OK PS#{problem.ps_id} ({provider}): {explanation[:60]}...")
            else:
                print(f"  [{i}/{total}] WARN PS#{problem.ps_id}: No explanation generated")
            
            db.commit()
            
            # Rate limiting: 1 request per second to respect API limits
            time.sleep(1.0)
            
        except Exception as e:
            errors += 1
            print(f"  [{i}/{total}] ERR PS#{problem.ps_id}: {type(e).__name__}: {str(e)[:60]}")
            db.rollback()
            continue
    
    summary = {
        "message": f"Processed {total} problems",
        "total_processed": total,
        "explanations_updated": updated,
        "titles_cleaned": titles_cleaned,
        "errors": errors,
        "providers_used": providers
    }
    
    print(f"\n{'='*60}")
    print(f"REGENERATION COMPLETE")
    print(f"  Updated: {updated}/{total}")
    print(f"  Titles cleaned: {titles_cleaned}")
    print(f"  Providers: {providers}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")
    
    return summary


# ============ Problem Endpoints ============

def _map_problem_to_response(problem: Problem, current_user: Optional[User] = None) -> dict:
    """Helper to map a Problem model to a unified dictionary response"""
    return {
        "ps_id": problem.ps_id,
        "title": problem.title,
        "description": problem.description,
        "source": problem.source,
        "source_id": problem.source_id,
        "date": problem.date,
        "suggested_tech": problem.suggested_tech,
        "author_name": problem.author_name,
        "author_id": problem.author_id,
        "reference_link": problem.reference_link,
        "tags": problem.tags or [],
        "scraped_at": problem.scraped_at,
        "difficulty_score": problem.difficulty_score or 0.0,
        "difficulty_level": problem.difficulty_level or 0,
        "upvotes": problem.upvotes or 0,
        "downvotes": problem.downvotes or 0,
        "comment_count": problem.comment_count or 0,
        "engagement_score": problem.engagement_score or 0.0,
        "text_length": problem.text_length or 0,
        "interested_count": len(problem.interested_users),
        "is_interested": current_user in problem.interested_users if current_user else False,
        # New cleaning/metadata fields
        "raw_title": problem.raw_title,
        "raw_tags": problem.raw_tags,
        "normalized_title": problem.normalized_title,
        "title_hash": problem.title_hash,
        "word_count": problem.word_count,
        "has_code_block": problem.has_code_block,
        "num_code_blocks": problem.num_code_blocks,
        "clean_version": problem.clean_version,
        # Engineering Impact Scoring (EIS)
        "technical_depth_score": problem.technical_depth_score or 0.0,
        "industry_impact_score": problem.industry_impact_score or 0.0,
        "cognitive_complexity_score": problem.cognitive_complexity_score or 0.0,
        "signal_quality_score": problem.signal_quality_score or 0.0,
        "engineering_impact_score": problem.engineering_impact_score or 0.0,
        # Humanized explanation (AI-generated plain English summary)
        "humanized_explanation": problem.humanized_explanation or "",
        # Collaboration Info
        "collaborators_count": sum(len(g.members) for g in problem.collaboration_groups if g.is_active),
        "squad_status": next((req.status for req in current_user.collaboration_requests if req.problem_id == problem.ps_id), "none") if current_user else "none"
    }

@app.get("/problems", response_model=List[ProblemResponse], tags=["Problems"])
def get_problems(
    skip: int = 0,
    limit: int = 100,
    tech: str = None,
    source: str = None,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Get all problems with optional filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **tech**: Filter by technology (e.g., 'python', 'react')
    - **source**: Filter by source platform (e.g., 'reddit', 'github')
    """
    # Try to get current user if token is provided
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass # Invalid token, treat as guest

    try:
        from sqlalchemy.orm import defer
        query = db.query(Problem).options(defer(Problem.embedding))
        
        # Apply filters
        if tech:
            query = query.filter(Problem.suggested_tech.contains(tech))
        if source:
            query = query.filter(Problem.source.contains(source))
        
        problems = query.order_by(Problem.scraped_at.desc()).offset(skip).limit(limit).all()
        
        return [_map_problem_to_response(p, current_user) for p in problems]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============ Search Endpoints ============

@app.get("/search/keyword", tags=["Search"])
def keyword_search(
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Keyword search across title, description, tags, and humanized_explanation.
    Uses SQL ILIKE for flexible matching.
    """
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass

    try:
        from sqlalchemy import or_, cast, String
        search_term = f"%{query.strip()}%"
        
        # Also split into individual words for broader matching
        words = [w for w in query.strip().split() if len(w) > 1]
        if not words:
            words = query.strip().split()
        
        # Build conditions: match full phrase OR individual words
        conditions = [
            Problem.title.ilike(search_term),
            Problem.description.ilike(search_term),
            Problem.humanized_explanation.ilike(search_term),
            Problem.suggested_tech.ilike(search_term),
        ]
        for word in words:
            w = f"%{word}%"
            conditions.extend([
                Problem.title.ilike(w),
                Problem.description.ilike(w),
                Problem.suggested_tech.ilike(w),   # match per-word in tech tags
                Problem.humanized_explanation.ilike(w),
            ])
        
        from sqlalchemy.orm import defer
        matching = db.query(Problem).options(defer(Problem.embedding)).filter(
            or_(*conditions)
        ).limit(limit * 2).all()  # Fetch extra for relevance sorting

        # Rank by relevance instead of EIS
        def relevance_score(p):
            score = 0
            title_lower = (p.title or '').lower()
            desc_lower = (p.description or '').lower()
            expl_lower = (p.humanized_explanation or '').lower()
            tech_lower = (p.suggested_tech or '').lower()
            full_query = query.strip().lower()
            # Full phrase match = highest boost
            if full_query in title_lower: score += 10
            if full_query in tech_lower: score += 5
            # Per-word matches
            for word in words:
                wl = word.lower()
                if wl in title_lower: score += 3
                if wl in tech_lower: score += 2
                if wl in expl_lower: score += 1
                if wl in desc_lower: score += 1
            return score
        
        matching.sort(key=relevance_score, reverse=True)
        problems = matching[:limit]

        results = [_map_problem_to_response(p, current_user) for p in problems]
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "search_type": "keyword"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/problems/trending", response_model=List[ProblemResponse], tags=["Problems"])
def get_trending_problems(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Get the top 15 most liked problems
    
    Returns problems with the highest 'interested_count' first.
    """
    from models import problem_interests
    from sqlalchemy import func
    
    # Try to get current user if token is provided
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass # Invalid token, treat as guest

    # We want to sort by the number of interested users.
    # A subquery counting interests per problem is efficient.
    interest_counts = db.query(
        problem_interests.c.problem_id,
        func.count(problem_interests.c.user_id).label('count')
    ).group_by(problem_interests.c.problem_id).subquery()

    # Join problems with the interest counts subquery
    problems = db.query(Problem).outerjoin(
        interest_counts, Problem.ps_id == interest_counts.c.problem_id
    ).order_by(
        func.coalesce(interest_counts.c.count, 0).desc(), 
        Problem.scraped_at.desc()
    ).limit(15).all()
    
    return [_map_problem_to_response(p, current_user) for p in problems]


@app.get("/problems/{problem_id}", response_model=ProblemDetailResponse, tags=["Problems"])
def get_problem_detail(
    problem_id: int, 
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get detailed information about a specific problem"""
    # Try to get current user if token is provided
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass # Invalid token, treat as guest

    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    response = _map_problem_to_response(problem, current_user)
    response["interested_users"] = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at,
            "is_premium": u.is_premium
        } for u in problem.interested_users
    ]
    
    return response


@app.post("/scrape", response_model=ScrapeResponse, tags=["Admin"])
def trigger_scrape(
    request: ScrapeRequest = ScrapeRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger scraping from configured platforms (admin only)
    """
    from scrapers.reddit_scraper import scrape_reddit
    from scrapers import scrape_github
    
    reddit_count = 0
    github_count = 0
    
    try:
        # Define quick_store helper once
        def quick_store(problems):
            from embedding_service import get_embedding_service
            from engineering_scoring_engine import get_scoring_engine
            
            embedding_service = get_embedding_service()
            scoring_engine = get_scoring_engine()
            
            count = 0
            cleaner = DataCleaner()
            for p_raw in problems:
                try:
                    # 1. Clean and enrich
                    p_data = cleaner.clean_problem(p_raw)
                    
                    # 2. Check for duplicate link
                    existing = db.query(Problem).filter(
                        Problem.reference_link == p_data['reference_link']
                    ).first()
                    if existing: continue
                    
                    # 3. Check for duplicate hash
                    existing_hash = db.query(Problem).filter(
                        Problem.title_hash == p_data['title_hash']
                    ).first()
                    if existing_hash: continue

                    # 4. Generate Semantic Embeddings on the fly
                    try:
                        emb = embedding_service.generate_embedding(
                            title=p_data.get('title', ''),
                            description=p_data.get('description', ''),
                            tags=p_data.get('tags', [])
                        )
                        if emb:
                            p_data['embedding'] = emb
                    except Exception as emb_e:
                        print(f"Embedding error during quick store: {emb_e}")

                    # 5. Calculate Engineering Impact Score (EIS)
                    try:
                        temp_problem = Problem(**p_data)
                        scores = scoring_engine.calculate_scores(temp_problem)
                        p_data.update(scores)
                    except Exception as score_err:
                        print(f"Scoring error during quick store: {score_err}")

                    new_p = Problem(**p_data)
                    db.add(new_p)
                    db.commit()
                    count += 1
                except Exception as e:
                    print(f"Quick store error: {e}")
                    db.rollback()
                    continue
            return count

        if "reddit" in request.platforms:
            reddit_problems = scrape_reddit(limit=request.limit)
            reddit_count = quick_store(reddit_problems)
        
        if "github" in request.platforms:
            github_problems = scrape_github(limit=request.limit)
            github_count = quick_store(github_problems)
        
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
    """
    from scrapers import scrape_github, scrape_stackoverflow, scrape_hackernews
    from sqlalchemy.exc import IntegrityError
    from difflib import SequenceMatcher
    
    # In-memory session-level dedupe
    seen_hashes = set()
    cleaner = DataCleaner()
    
    total_processed = 0
    total_cleaned = 0
    total_deduped = 0
    records_with_code = 0
    
    source_results = {
        "github": 0,
        "stackoverflow": 0,
        "hackernews": 0,
        "reddit": 0
    }

    def is_duplicate(cleaned_data: dict, db: Session) -> bool:
        # Layer 1: Reference link
        existing_link = db.query(Problem).filter(
            Problem.reference_link == cleaned_data['reference_link']
        ).first()
        if existing_link: return True
        
        # Layer 2: Title Hash
        existing_hash = db.query(Problem).filter(
            Problem.title_hash == cleaned_data['title_hash']
        ).first()
        if existing_hash: return True
        
        # Layer 3: Session check
        if cleaned_data['title_hash'] in seen_hashes: return True
        
        return False

    def insert_problems(problems_raw, source_key):
        from embedding_service import get_embedding_service
        from engineering_scoring_engine import get_scoring_engine
        embedding_service = get_embedding_service()
        
        inserted_problems = []
        deduped = 0
        nonlocal total_cleaned, records_with_code
        
        for p_raw in problems_raw:
            try:
                # 1. Clean
                cleaned_p = cleaner.clean_problem(p_raw)
                total_cleaned += 1
                if cleaned_p['has_code_block']:
                    records_with_code += 1
                
                # 2. Quality Gate — reject trash/non-English/gibberish
                passes, reject_reason = cleaner.passes_quality_gate(cleaned_p)
                if not passes:
                    safe_title = (cleaned_p.get('title', '') or '')[:60]
                    try:
                        safe_title = safe_title.encode('ascii', errors='replace').decode('ascii')
                    except:
                        safe_title = '[encoding error]'
                    print(f"[QUALITY GATE] Rejected ({reject_reason}): {safe_title}")
                    deduped += 1  # Count as filtered
                    continue
                
                # 3. Deduplicate
                if is_duplicate(cleaned_p, db):
                    deduped += 1
                    continue
                
                # 3. Insert and Score
                
                # Apply Semantic Embeddings on the fly
                try:
                    emb = embedding_service.generate_embedding(
                        title=cleaned_p.get('title', ''),
                        description=cleaned_p.get('description', ''),
                        tags=cleaned_p.get('tags', [])
                    )
                    if emb:
                        cleaned_p['embedding'] = emb
                except Exception as emb_e:
                    print(f"Embedding error during insert_problems: {emb_e}")

                new_problem = Problem(**cleaned_p)
                
                # Apply Engineering Impact Scoring
                try:
                    scoring_engine = get_scoring_engine()
                    scores = scoring_engine.calculate_scores(new_problem)
                    for attr, val in scores.items():
                        setattr(new_problem, attr, val)
                except Exception as score_err:
                    print(f"Scoring error for problem: {score_err}")
                
                db.add(new_problem)
                db.commit()
                db.refresh(new_problem) # Ensure we have the ps_id
                
                seen_hashes.add(cleaned_p['title_hash'])
                inserted_problems.append(new_problem)
            except Exception as e:
                print(f"Insertion error ({source_key}): {e}")
                db.rollback()
                continue
        
        return inserted_problems, deduped
    
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
        
        all_new_problems_objects = []
        
        # PHASE 1: Initial scraping (10 from each source)
        print(f"\n📥 PHASE 1: Initial Scraping ({INITIAL_PER_SOURCE} per source)")
        print("-" * 70)
        
        # Scrape GitHub
        print(f"\n[1/3] GitHub...")
        try:
            github_problems = scrape_github(limit=INITIAL_PER_SOURCE)
            github_fetched = len(github_problems)
            github_new, github_dups = insert_problems(github_problems, "github")
            all_new_problems_objects.extend(github_new)
            github_count = len(github_new)
            total_duplicates += github_dups
            source_results["github"] = github_count
            print(f"  ✅ GitHub: {github_count} inserted, {github_dups} duplicates")
        except Exception as e:
            print(f"  ❌ GitHub scraping failed: {str(e)[:100]}")
            github_problems = []
        
        # Scrape Stack Overflow
        print(f"\n[2/3] Stack Overflow...")
        try:
            stackoverflow_problems = scrape_stackoverflow(limit=INITIAL_PER_SOURCE)
            stackoverflow_fetched = len(stackoverflow_problems)
            stackoverflow_new, so_dups = insert_problems(stackoverflow_problems, "stackoverflow")
            all_new_problems_objects.extend(stackoverflow_new)
            stackoverflow_count = len(stackoverflow_new)
            total_duplicates += so_dups
            source_results["stackoverflow"] = stackoverflow_count
            print(f"  ✅ Stack Overflow: {stackoverflow_count} inserted, {so_dups} duplicates")
        except Exception as e:
            print(f"  ❌ Stack Overflow scraping failed: {str(e)[:100]}")
            stackoverflow_problems = []
        
        # Scrape Hacker News
        print(f"\n[3/3] Hacker News...")
        try:
            hackernews_problems = scrape_hackernews(limit=INITIAL_PER_SOURCE)
            hackernews_fetched = len(hackernews_problems)
            hackernews_new, hn_dups = insert_problems(hackernews_problems, "hackernews")
            all_new_problems_objects.extend(hackernews_new)
            hackernews_count = len(hackernews_new)
            total_duplicates += hn_dups
            source_results["hackernews"] = hackernews_count
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
                            extra_new, extra_dups = insert_problems(extra_github, "github")
                            all_new_problems_objects.extend(extra_new)
                            github_count += len(extra_new)
                            source_results["github"] = github_count
                            github_fetched += len(extra_github)
                            total_duplicates += extra_dups
                            current_total += len(extra_new)
                            print(f"    GitHub: +{len(extra_new)} ({extra_dups} dups)")
                    except:
                        pass
                
                # Additional Stack Overflow
                if current_total < TARGET_TOTAL:
                    try:
                        extra_so = scrape_stackoverflow(limit=additional_per_source)
                        if extra_so:
                            extra_new, extra_dups = insert_problems(extra_so, "stackoverflow")
                            all_new_problems_objects.extend(extra_new)
                            stackoverflow_count += len(extra_new)
                            source_results["stackoverflow"] = stackoverflow_count
                            stackoverflow_fetched += len(extra_so)
                            total_duplicates += extra_dups
                            current_total += len(extra_new)
                            print(f"    Stack Overflow: +{len(extra_new)} ({extra_dups} dups)")
                    except:
                        pass
                
                # Additional Hacker News
                if current_total < TARGET_TOTAL:
                    try:
                        extra_hn = scrape_hackernews(limit=additional_per_source)
                        if extra_hn:
                            extra_new, extra_dups = insert_problems(extra_hn, "hackernews")
                            all_new_problems_objects.extend(extra_new)
                            hackernews_count += len(extra_new)
                            source_results["hackernews"] = hackernews_count
                            hackernews_fetched += len(extra_hn)
                            total_duplicates += extra_dups
                            current_total += len(extra_new)
                            print(f"    Hacker News: +{len(extra_new)} ({extra_dups} dups)")
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
        
        # COLLECT ALL NEW PROBLEMS (Safely)
        all_new_problems = []
        try:
            for p in all_new_problems_objects:
                 try:
                      all_new_problems.append(_map_problem_to_response(p, None))
                 except Exception as e:
                      print(f"Mapping error for problem {getattr(p, 'ps_id', 'unknown')}: {e}")
        except Exception as e:
            print(f"Error collecting all new problems: {e}")

        return {
            "message": f"Successfully scraped {current_total} new problems ({total_duplicates} duplicates skipped)",
            "total_scraped": current_total,
            "total_fetched": github_fetched + stackoverflow_fetched + hackernews_fetched,
            "total_cleaned": total_cleaned,
            "records_with_code": records_with_code,
            "github_count": github_count,
            "github_fetched": github_fetched,
            "stackoverflow_count": stackoverflow_count,
            "stackoverflow_fetched": stackoverflow_fetched,
            "hackernews_count": hackernews_count,
            "hackernews_fetched": hackernews_fetched,
            "duplicates_skipped": total_duplicates,
            "target_per_source": INITIAL_PER_SOURCE,
            "target_total": TARGET_TOTAL,
            "new_problems": all_new_problems
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
    from models import problem_interests
    from sqlalchemy import select, delete, insert, func
    
    # Find the problem
    problem = db.query(Problem).filter(Problem.ps_id == request.problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Check if user already marked interest using direct query
    stmt = select(problem_interests).where(
        problem_interests.c.user_id == current_user.id,
        problem_interests.c.problem_id == problem.ps_id
    )
    existing = db.execute(stmt).first()
    
    if existing:
        # Get count
        count_stmt = select(func.count()).select_from(problem_interests).where(problem_interests.c.problem_id == problem.ps_id)
        total = db.execute(count_stmt).scalar() or 0
        return {
            "message": "Already marked as interested",
            "total_interested": total
        }
    
    # Add interest direct insert
    db.execute(insert(problem_interests).values(user_id=current_user.id, problem_id=problem.ps_id))
    db.commit()
    
    # Get total count for problem
    count_stmt = select(func.count()).select_from(problem_interests).where(problem_interests.c.problem_id == problem.ps_id)
    total = db.execute(count_stmt).scalar() or 0
    
    print(f"MARK INTEREST SUCCESS: User {current_user.id} -> Problem {problem.ps_id}. New Total: {total}")
    
    return {
        "message": "Interest marked successfully",
        "total_interested": total
    }


@app.delete("/interest/{problem_id}", tags=["Collaboration"])
def remove_interest(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove interest from a problem"""
    from models import problem_interests
    from sqlalchemy import delete, select, func
    
    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    # Direct delete
    stmt = delete(problem_interests).where(
        problem_interests.c.user_id == current_user.id,
        problem_interests.c.problem_id == problem.ps_id
    )
    db.execute(stmt)
    db.commit()
    
    # Get total count for problem after deletion
    count_stmt = select(func.count()).select_from(problem_interests).where(problem_interests.c.problem_id == problem.ps_id)
    total = db.execute(count_stmt).scalar() or 0
    
    print(f"REMOVE INTEREST: User {current_user.id} -> Problem {problem.ps_id}. New Total: {total}")
    
    return {
        "message": "Interest removed successfully",
        "total_interested": total
    }


@app.get("/me/interests", response_model=List[ProblemResponse], tags=["Authentication"])
def get_user_interests(
    current_user: User = Depends(get_current_user)
):
    """Get the list of problems the current user is interested in"""
    result = []
    for problem in current_user.interested_problems:
        result.append(_map_problem_to_response(problem, current_user))
    
    return result

@app.get("/me/squads", response_model=List[ProblemResponse], tags=["Authentication"])
def get_user_squads(
    current_user: User = Depends(get_current_user)
):
    """Get the list of problems the current user is collaborating on"""
    result = []
    # Only return problems where the request is 'accepted'
    for req in current_user.collaboration_requests:
        if req.status == "accepted":
            result.append(_map_problem_to_response(req.problem, current_user))
    
    return result


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
    
    # Auto-mark interest if not already done
    if current_user not in problem.interested_users:
        from models import problem_interests
        from sqlalchemy import insert
        db.execute(insert(problem_interests).values(user_id=current_user.id, problem_id=problem.ps_id))
        db.commit()
        db.refresh(problem)
        print(f"AUTO-INTEREST: User {current_user.id} -> Problem {problem.ps_id}")
    
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
    # Now simplified: can request if they don't already have one
    can_request = user_request is None
    reason = None
    
    if not can_request:
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



# ============ Squad System (New) ============

from typing import DefaultDict
from collections import defaultdict

class ConnectionManager:
    """Manages active WebSocket connections per squad."""
    def __init__(self):
        self.active: DefaultDict[int, list] = defaultdict(list)  # squad_id -> list of WebSocket

    async def connect(self, squad_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[squad_id].append(websocket)

    def disconnect(self, squad_id: int, websocket: WebSocket):
        self.active[squad_id].remove(websocket)

    async def broadcast(self, squad_id: int, message: dict):
        import json
        for ws in list(self.active[squad_id]):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.disconnect(squad_id, ws)

ws_manager = ConnectionManager()


def _squad_member_ids(squad: CollaborationGroup) -> set:
    return {m.id for m in squad.members}


@app.get("/squads", tags=["Squads"])
def list_squads(db: Session = Depends(get_db)):
    """List all public squads with description, member count, and problem title."""
    squads = db.query(CollaborationGroup).filter(CollaborationGroup.is_active == True).all()
    result = []
    for sq in squads:
        pending_count = sum(1 for r in sq.join_requests if r.status == 'pending')
        result.append({
            "id": sq.id,
            "name": sq.name or f"Squad #{sq.id}",
            "description": sq.description or "",
            "problem_id": sq.problem_id,
            "problem_title": sq.problem.title if sq.problem else "",
            "leader_id": sq.leader_id,
            "leader_username": sq.leader.username if sq.leader else "Unknown",
            "member_count": len(sq.members),
            "pending_requests": pending_count,
            "created_at": sq.created_at,
        })
    return result


@app.post("/squads", tags=["Squads"])
def create_squad(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new squad. The caller becomes the leader and is added as the first member.
    Required fields: problem_id (int), name (str), description (str)
    """
    problem_id = payload.get("problem_id")
    name = payload.get("name", "").strip()
    description = payload.get("description", "").strip()

    if not problem_id or not name:
        raise HTTPException(status_code=400, detail="problem_id and name are required")

    problem = db.query(Problem).filter(Problem.ps_id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    squad = CollaborationGroup(
        problem_id=problem_id,
        name=name,
        description=description,
        leader_id=current_user.id,
        is_active=True,
    )
    squad.members.append(current_user)
    db.add(squad)
    db.commit()
    db.refresh(squad)

    return {
        "id": squad.id,
        "name": squad.name,
        "description": squad.description,
        "problem_id": squad.problem_id,
        "leader_id": squad.leader_id,
        "message": "Squad created! Share it with others."
    }


@app.get("/squads/{squad_id}", tags=["Squads"])
def get_squad(
    squad_id: int,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Get squad details. Members list is only visible to accepted members."""
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass

    is_member = current_user and current_user.id in _squad_member_ids(squad)
    is_leader = current_user and current_user.id == squad.leader_id

    user_request = None
    pending_requests = []
    if current_user:
        user_request = db.query(SquadJoinRequest).filter(
            SquadJoinRequest.squad_id == squad_id,
            SquadJoinRequest.user_id == current_user.id
        ).first()

    if is_leader:
        pending_requests = [
            {"request_id": r.id, "user_id": r.user_id, "username": r.user.username, "created_at": r.created_at}
            for r in squad.join_requests if r.status == 'pending'
        ]

    return {
        "id": squad.id,
        "name": squad.name or f"Squad #{squad.id}",
        "description": squad.description or "",
        "problem_id": squad.problem_id,
        "problem_title": squad.problem.title if squad.problem else "",
        "leader_id": squad.leader_id,
        "leader_username": squad.leader.username if squad.leader else "Unknown",
        "member_count": len(squad.members),
        "members": [{"id": m.id, "username": m.username} for m in squad.members] if is_member else [],
        "is_member": is_member,
        "is_leader": is_leader,
        "user_request_status": user_request.status if user_request else None,
        "pending_requests": pending_requests,
        "created_at": squad.created_at,
    }


@app.post("/squads/{squad_id}/join", tags=["Squads"])
def join_squad(
    squad_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request to join a squad."""
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id, CollaborationGroup.is_active == True).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    if current_user.id in _squad_member_ids(squad):
        raise HTTPException(status_code=400, detail="You are already a member of this squad")

    existing = db.query(SquadJoinRequest).filter(
        SquadJoinRequest.squad_id == squad_id,
        SquadJoinRequest.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"You already have a join request (status: {existing.status})")

    join_req = SquadJoinRequest(squad_id=squad_id, user_id=current_user.id, status='pending')
    db.add(join_req)
    db.commit()
    return {"message": "Join request sent! The squad leader will review it.", "status": "pending"}


@app.post("/squads/{squad_id}/accept/{user_id}", tags=["Squads"])
def accept_squad_member(
    squad_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Squad leader accepts a join request."""
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad or squad.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the squad leader can accept members")

    join_req = db.query(SquadJoinRequest).filter(
        SquadJoinRequest.squad_id == squad_id,
        SquadJoinRequest.user_id == user_id
    ).first()
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")

    join_req.status = 'accepted'
    new_member = db.query(User).filter(User.id == user_id).first()
    if new_member and new_member not in squad.members:
        squad.members.append(new_member)
    db.commit()
    return {"message": f"{new_member.username} has been accepted into the squad!", "member_count": len(squad.members)}


@app.post("/squads/{squad_id}/reject/{user_id}", tags=["Squads"])
def reject_squad_member(
    squad_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Squad leader rejects a join request."""
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad or squad.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the squad leader can reject members")

    join_req = db.query(SquadJoinRequest).filter(
        SquadJoinRequest.squad_id == squad_id,
        SquadJoinRequest.user_id == user_id
    ).first()
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")

    join_req.status = 'rejected'
    db.commit()
    return {"message": "Join request rejected."}


@app.get("/squads/{squad_id}/messages", tags=["Squads"])
def get_squad_messages(
    squad_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Fetch the most recent N chat messages for a squad (members only)."""
    current_user = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            from auth import verify_token
            email = verify_token(token)
            current_user = db.query(User).filter(User.email == email).first()
        except:
            pass

    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    if not current_user or current_user.id not in _squad_member_ids(squad):
        raise HTTPException(status_code=403, detail="Only squad members can view messages")

    messages = db.query(SquadMessage).filter(
        SquadMessage.squad_id == squad_id
    ).order_by(SquadMessage.sent_at.asc()).limit(limit).all()

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_username": m.sender.username,
            "content": m.content,
            "sent_at": m.sent_at.isoformat()
        } for m in messages
    ]


@app.delete("/squads/{squad_id}", tags=["Squads"])
def delete_squad(
    squad_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Squad leader deletes a squad."""
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    if squad.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the squad leader can delete this squad")

    # Mark as inactive instead of hard deleting to preserve referential integrity if needed,
    # or hard delete. Since we have messages and join requests, let's hard delete them first or cascade.
    db.query(SquadMessage).filter(SquadMessage.squad_id == squad_id).delete()
    db.query(SquadJoinRequest).filter(SquadJoinRequest.squad_id == squad_id).delete()
    db.delete(squad)
    db.commit()
    return {"message": "Squad deleted successfully."}


@app.post("/squads/{squad_id}/leave", tags=["Squads"])
def leave_squad(
    squad_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Member leaves a squad."""
    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id, CollaborationGroup.is_active == True).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    if squad.leader_id == current_user.id:
        raise HTTPException(status_code=400, detail="The leader cannot leave the squad. You must delete it.")

    if current_user not in squad.members:
        raise HTTPException(status_code=400, detail="You are not a member of this squad")

    # Remove user from group
    squad.members.remove(current_user)
    
    # Also clean up their join request if it exists
    db.query(SquadJoinRequest).filter(
        SquadJoinRequest.squad_id == squad_id,
        SquadJoinRequest.user_id == current_user.id
    ).delete()

    db.commit()
    return {"message": "You have left the squad."}


@app.websocket("/ws/squad/{squad_id}")
async def squad_websocket(
    websocket: WebSocket,
    squad_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time squad chat.
    Connect with: ws://localhost:8000/ws/squad/{squad_id}?token=<jwt>
    Messages are persisted to DB and broadcast to all connected members.
    """
    import json
    from auth import verify_token

    # Authenticate via token query param
    current_user = None
    try:
        email = verify_token(token)
        current_user = db.query(User).filter(User.email == email).first()
    except Exception:
        await websocket.close(code=4001)
        return

    if not current_user:
        await websocket.close(code=4001)
        return

    squad = db.query(CollaborationGroup).filter(CollaborationGroup.id == squad_id).first()
    if not squad or current_user.id not in _squad_member_ids(squad):
        await websocket.close(code=4003)
        return

    await ws_manager.connect(squad_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            content = (data.get("content") or "").strip()
            if not content:
                continue

            # Persist message
            msg = SquadMessage(squad_id=squad_id, sender_id=current_user.id, content=content)
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Broadcast to all members in the squad
            broadcast_payload = {
                "id": msg.id,
                "sender_id": current_user.id,
                "sender_username": current_user.username,
                "content": content,
                "sent_at": msg.sent_at.isoformat()
            }
            await ws_manager.broadcast(squad_id, broadcast_payload)
    except WebSocketDisconnect:
        ws_manager.disconnect(squad_id, websocket)


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

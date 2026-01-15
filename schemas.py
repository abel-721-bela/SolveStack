from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime

# ============ User Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    email: str
    username: str
    created_at: datetime
    is_premium: bool
    
    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    email: Optional[str] = None

# ============ Problem Schemas ============

class ProblemBase(BaseModel):
    """Base schema for problem"""
    title: str
    description: Optional[str] = None
    source: str
    date: str
    suggested_tech: str
    author_name: str
    author_id: str
    reference_link: str
    tags: List[str] = []

class ProblemResponse(ProblemBase):
    """Schema for problem in responses"""
    ps_id: int
    scraped_at: datetime
    interested_count: int = 0  # Will be computed
    
    # Phase 4: Multi-Source Fields (optional for backward compatibility)
    source_id: Optional[str] = None
    humanized_explanation: Optional[str] = None
    solution_possibility: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProblemDetailResponse(ProblemResponse):
    """Detailed problem with interested users"""
    interested_users: List[UserResponse] = []
    
    class Config:
        from_attributes = True

# ============ Interest Schemas ============

class InterestRequest(BaseModel):
    """Schema for marking interest in a problem"""
    problem_id: int

class InterestResponse(BaseModel):
    """Schema for interest response"""
    message: str
    total_interested: int

# ============ Collaboration Schemas ============

class CollaborationRequestCreate(BaseModel):
    """Schema for creating a collaboration request"""
    problem_id: int

class CollaborationActionRequest(BaseModel):
    """Schema for accepting or rejecting a collaboration request"""
    problem_id: int

class CollaborationRequestResponse(BaseModel):
    """Schema for collaboration request responses"""
    request_id: int
    problem_id: int
    status: str
    message: str
    created_at: datetime
    group_created: bool = False
    group_id: Optional[int] = None
    total_members: Optional[int] = None
    collaborators: Optional[List[str]] = None

class CollaborationGroupInfo(BaseModel):
    """Schema for collaboration group information"""
    group_id: int
    member_count: int
    members: List[str]  # Usernames
    created_at: datetime
    is_active: bool

class CollaborationStatusResponse(BaseModel):
    """Schema for getting collaboration status on a problem"""
    problem_id: int
    problem_title: str
    your_request: Optional[dict] = None
    total_requests: int
    pending_requests: int
    accepted_requests: int
    active_group: Optional[CollaborationGroupInfo] = None
    can_request: bool
    reason: Optional[str] = None

# ============ Scraping Schemas ============

class ScrapeRequest(BaseModel):
    """Schema for triggering scrape"""
    limit: int = Field(default=20, ge=1, le=100)
    platforms: List[str] = Field(default=["reddit", "github"])

class ScrapeResponse(BaseModel):
    """Schema for scrape response"""
    message: str
    total_scraped: int
    reddit_count: int = 0
    github_count: int = 0

class ScrapeAllResponse(BaseModel):
    """Schema for unified /scrape/all endpoint response"""
    message: str
    total_scraped: int
    github_count: int = 0
    stackoverflow_count: int = 0
    hackernews_count: int = 0
    duplicates_skipped: int = 0

# ============ Phase 2C: Quality Scoring & Matching Schemas ============

class QualityScoreBreakdown(BaseModel):
    """Component scores for quality scoring"""
    score: int
    max: int
    reasons: List[str]

class QualityScoreResponse(BaseModel):
    """Response for problem quality scoring"""
    problem_id: int
    quality_score: int  # 0-100
    difficulty: str  # Beginner/Intermediate/Advanced
    estimated_effort: str  # Time estimate
    breakdown: Dict[str, QualityScoreBreakdown]
    message: str

class RecommendationItem(BaseModel):
    """Single problem recommendation"""
    problem_id: int
    title: str
    suggested_tech: str
    difficulty: str
    estimated_effort: str
    quality_score: int
    match_score: int  # 0-100
    reasons: List[str]  # Why recommended
    
class RecommendationsResponse(BaseModel):
    """Response for GET /recommendations"""
    user_id: int
    username: str
    total_recommendations: int
    recommendations: List[RecommendationItem]

class CollaboratorSuggestion(BaseModel):
    """Single collaborator suggestion"""
    user_id: int
    username: str
    skills: List[str]
    experience_level: str
    compatibility_score: int  # 0-100
    reasons: List[str]  # Why compatible

class CollaborationSuggestionsResponse(BaseModel):
    """Response for GET /collaborate/suggestions/{problem_id}"""
    problem_id: int
    problem_title: str
    total_suggestions: int
    suggestions: List[CollaboratorSuggestion]

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime, date as date_type

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
    interested_count: int = 0
    squads_count: int = 0
    skills: List[str] = []
    interests: List[str] = []
    activity_score: int = 0
    
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
    date: date_type
    suggested_tech: str
    author_name: str
    author_id: str
    reference_link: str
    tags: Optional[List[str]] = [] # Legacy tags field
    
    # Raw Fields
    raw_title: Optional[str] = None
    raw_description: Optional[str] = None
    raw_tags: Optional[List[str]] = []
    
    # Processed Fields
    cleaned_title: Optional[str] = None
    cleaned_description: Optional[str] = None
    normalized_title: Optional[str] = None
    title_hash: Optional[str] = None
    
    # Scoring and Metadata
    source_id: Optional[str] = None
    difficulty_score: float = 0.0
    difficulty_level: int = 0
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    engagement_score: float = 0.0
    
    # Metrics
    text_length: Optional[int] = 0
    word_count: Optional[int] = 0
    has_code_block: Optional[bool] = False
    num_code_blocks: Optional[int] = 0
    
    # Versioning
    cleaned_at: Optional[datetime] = None
    clean_version: Optional[str] = "1.0.0"
    
    # Humanized explanation
    humanized_explanation: Optional[str] = None
    
    # Semantic Search Support
    embedding: Optional[List[float]] = None

class ProblemResponse(ProblemBase):
    """Schema for problem in responses"""
    ps_id: int
    scraped_at: datetime
    interested_count: int = 0  # Will be computed
    is_interested: bool = False  # True if current user marked interest
    
    # EIS Score
    engineering_impact_score: Optional[float] = 0.0
    technical_depth_score: Optional[float] = 0.0
    industry_impact_score: Optional[float] = 0.0
    cognitive_complexity_score: Optional[float] = 0.0
    signal_quality_score: Optional[float] = 0.0
    
    # Collaboration Info
    collaborators_count: int = 0
    squad_status: Optional[str] = "none" # pending/accepted/rejected/none

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

class HybridSearchResponse(BaseModel):
    """Schema for hybrid search result"""
    ps_id: int
    title: str
    description: Optional[str] = None
    semantic_score: float
    keyword_score: float
    tag_score: float
    final_score: float

    class Config:
        from_attributes = True

class SemanticSearchResult(BaseModel):
    """Schema for a single semantic search result"""
    ps_id: int
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    semantic_score: float

class SemanticSearchMetadata(BaseModel):
    """Metadata for semantic search performance and model info"""
    model: Optional[str] = None
    embedding_dim: Optional[int] = None
    normalized: Optional[bool] = None
    query_time_ms: Optional[float] = None
    db_time_ms: Optional[float] = None
    total_time_ms: Optional[float] = None
    # For intent-aware search reuse
    latency_ms: Optional[float] = None
    stage1_candidates: Optional[int] = None
    reranking: Optional[str] = None
    processed_query: Optional[dict] = None

class SemanticSearchResponse(BaseModel):
    """Full response for semantic search"""
    query: str
    results: List[SemanticSearchResult]
    metadata: SemanticSearchMetadata

class SearchResultScores(BaseModel):
    semantic: float
    keyword: float
    tag: float
    final: float

class IntentAwareSearchResult(BaseModel):
    ps_id: int
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    scores: SearchResultScores

class IntentAwareSearchMetadata(BaseModel):
    latency_ms: float
    stage1_candidates: int
    reranking: str
    processed_query: Optional[dict] = None

class IntentAwareSearchResponse(BaseModel):
    query: str
    results: List[IntentAwareSearchResult]
    metadata: IntentAwareSearchMetadata

class ShelfQueryResult(BaseModel):
    id: int
    title: str
    engineering_impact_score: float
    technical_depth_score: float
    industry_impact_score: float
    cognitive_complexity_score: float
    signal_quality_score: float
    tags: Optional[List[str]] = []

class ShelfResponse(BaseModel):
    mode: str
    total_found: int
    results: List[ShelfQueryResult]

class ImpactExplanation(BaseModel):
    problem_id: int
    engineering_impact_score: float
    breakdown: dict
    explanation: str
    thinking_type: str
    signals_contributed: List[str]

class EISDistribution(BaseModel):
    bucket: str
    count: int

class ShelfAnalytics(BaseModel):
    total_analyzed: int
    low_signal_percentage: float
    avg_impact_score: float
    top_impact_problems: List[dict]
    eis_distribution: List[EISDistribution]

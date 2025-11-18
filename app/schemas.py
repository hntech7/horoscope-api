from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime
from beanie import PydanticObjectId

# Generic type for response data
T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None
    
    @classmethod
    def success_response(cls, data: T = None, message: str = "Operation successful"):
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(cls, message: str, error: str = None):
        return cls(success=False, message=message, error=error)

class UserBase(BaseModel):
    name: str
    language: str
    email: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    zodiac_sign: Optional[str] = None
    occupation: Optional[str] = None
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    user_id: str
    provider: Optional[str] = None
    provider_id: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    email: Optional[EmailStr] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    zodiac_sign: Optional[str] = None
    occupation: Optional[str] = None
    profile_image: Optional[str] = None

class UserResponse(UserBase):
    id: PydanticObjectId = Field(alias="_id")
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True, "populate_by_name": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class LogoutResponse(BaseModel):
    message: str

class SocialLoginRequest(BaseModel):
    provider_id: str  # The user ID from Google/Apple
    provider: str  # 'google' or 'apple'
    name: str
    email: Optional[str] = None
    profile_image: Optional[str] = None
    language: str = "en"  # Default language


# Conversation schemas
class ChatBase(BaseModel):
    query: str
    answer: str
    timestamp: Optional[datetime] = None

class ChatResponse(ChatBase):
    timestamp: datetime

class ConversationRequest(BaseModel):
    conversationId: Optional[str] = None
    query: str
    answer: str

class ConversationResponse(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    userId: str = Field(alias="user_id")
    chats: List[ChatResponse]
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")
    
    model_config = {"from_attributes": True, "populate_by_name": True}

class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int


# Credit system schemas
class CreditBalanceResponse(BaseModel):
    balance: int
    total_earned: int
    total_spent: int
    updated_at: datetime

class FeatureUsageRequest(BaseModel):
    feature_type: str
    session_duration: Optional[int] = None  # Duration in minutes

class CreditTransactionResponse(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    transaction_type: str
    amount: int
    feature_type: Optional[str] = None
    credit_type: Optional[str] = None
    description: str
    balance_before: int
    balance_after: int
    created_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}

class CreditTransactionListResponse(BaseModel):
    transactions: List[CreditTransactionResponse]
    total: int

class AddCreditsRequest(BaseModel):
    amount: int
    credit_type: str  # 'purchase' or 'ad_watch'
    description: Optional[str] = None

# Analytics schemas
class FeatureUsageStats(BaseModel):
    feature_name: str
    usage_count: int
    total_credits_spent: int

class UserAnalyticsResponse(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    user_id: str
    feature_usage: dict
    total_sessions: int
    last_active: datetime
    total_time_spent: int
    favorite_features: List[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}

class AnalyticsSummaryResponse(BaseModel):
    total_users: int
    active_users_today: int
    active_users_this_week: int
    active_users_this_month: int
    most_popular_features: List[FeatureUsageStats]
    total_credits_consumed: int
    average_session_duration: float

class UserActivityRequest(BaseModel):
    session_duration: int  # Duration in minutes
    features_used: List[str] = Field(default_factory=list)

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from pymongo import IndexModel
from enum import Enum

class User(Document):
    user_id: Indexed(str, unique=True)  # Unique identifier
    name: str
    email: Optional[Indexed(str, unique=True)] = None
    language: str
    birth_date: Optional[str] = None  # Format: YYYY-MM-DD
    birth_time: Optional[str] = None  # Format: HH:MM
    zodiac_sign: Optional[str] = None
    occupation: Optional[str] = None
    profile_image: Optional[str] = None  # URL or base64 string
    
    # Social login fields
    provider: Optional[str] = None  # 'google', 'apple', or None for regular users
    provider_id: Optional[str] = None  # ID from the social provider
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            IndexModel([("provider", 1), ("provider_id", 1)], unique=True, sparse=True),
        ]
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', name='{self.name}', email='{self.email}')>"


class TokenBlacklist(Document):
    """Model to store blacklisted tokens"""
    token: Indexed(str, unique=True)  # The JWT token
    user_id: str  # User who owns the token
    blacklisted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # When the token would naturally expire
    
    class Settings:
        name = "token_blacklist"
        indexes = [
            IndexModel([("expires_at", 1)], expireAfterSeconds=0),  # TTL index to auto-delete expired tokens
        ]
    
    def __repr__(self):
        return f"<TokenBlacklist(user_id='{self.user_id}', blacklisted_at='{self.blacklisted_at}')>"


class RefreshToken(Document):
    """Model to store refresh tokens"""
    token: Indexed(str, unique=True)  # The refresh token
    user_id: str  # User who owns the token
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # When the refresh token expires
    is_active: bool = True  # Whether the token is still valid
    
    class Settings:
        name = "refresh_tokens"
        indexes = [
            IndexModel([("expires_at", 1)], expireAfterSeconds=0),  # TTL index to auto-delete expired tokens
            IndexModel([("user_id", 1)]),
        ]
    
    def __repr__(self):
        return f"<RefreshToken(user_id='{self.user_id}', created_at='{self.created_at}', is_active='{self.is_active}')>"


class Chat(BaseModel):
    """Individual chat within a conversation"""
    query: str
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(Document):
    """Model to store conversations"""
    user_id: str  # User who owns the conversation
    chats: List[Chat] = Field(default_factory=list)  # List of chats in the conversation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "conversations"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("created_at", -1)]),
        ]
    
    def __repr__(self):
        return f"<Conversation(user_id='{self.user_id}', chats_count={len(self.chats)}, created_at='{self.created_at}')>"


class FeatureType(str, Enum):
    """Enum for different feature types and their credit costs"""
    CHAT = "chat"
    DAILY_INSIGHTS = "daily_insights"
    COMPATIBILITY = "compatibility"
    LUCKY_ELEMENTS = "lucky_elements"
    MOOD_FORECAST = "mood_forecast"
    ASTRO_REMEDIES = "astro_remedies"
    AFFIRMATIONS = "affirmations"
    DREAM_GUIDE = "dream_guide"


# Feature credit costs mapping
FEATURE_COSTS = {
    FeatureType.CHAT: 3,
    FeatureType.DAILY_INSIGHTS: 4,
    FeatureType.COMPATIBILITY: 3,
    FeatureType.LUCKY_ELEMENTS: 1,
    FeatureType.MOOD_FORECAST: 2,
    FeatureType.ASTRO_REMEDIES: 3,
    FeatureType.AFFIRMATIONS: 3,
    FeatureType.DREAM_GUIDE: 3,
}


class UserCredits(Document):
    """Model to store user credit balance"""
    user_id: Indexed(str, unique=True)  # User identifier
    balance: int = Field(default=10)  # Initial balance of 10 credits
    total_earned: int = Field(default=10)  # Total credits earned (including initial)
    total_spent: int = Field(default=0)  # Total credits spent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_credits"
        indexes = [
            IndexModel([("user_id", 1)], unique=True),
        ]
    
    def __repr__(self):
        return f"<UserCredits(user_id='{self.user_id}', balance={self.balance})>"


class CreditTransaction(Document):
    """Model to store credit transaction history"""
    user_id: str  # User who made the transaction
    transaction_type: str  # 'debit' or 'credit'
    amount: int  # Number of credits
    feature_type: Optional[FeatureType] = None  # Feature used (for debit transactions)
    credit_type: Optional[str] = None  # 'purchase' or 'ad_watch' (for credit transactions)
    description: str  # Description of the transaction
    balance_before: int  # Balance before transaction
    balance_after: int  # Balance after transaction
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "credit_transactions"
        indexes = [
            IndexModel([("user_id", 1)]),
            IndexModel([("created_at", -1)]),
            IndexModel([("feature_type", 1)]),
            IndexModel([("transaction_type", 1)]),
        ]
    
    def __repr__(self):
        return f"<CreditTransaction(user_id='{self.user_id}', type='{self.transaction_type}', amount={self.amount})>"


class UserAnalytics(Document):
    """Model to store user analytics data"""
    user_id: str  # User identifier
    feature_usage: dict = Field(default_factory=dict)  # Usage count per feature
    total_sessions: int = Field(default=0)  # Total app sessions
    last_active: datetime = Field(default_factory=datetime.utcnow)  # Last activity timestamp
    total_time_spent: int = Field(default=0)  # Total time spent in minutes
    favorite_features: List[str] = Field(default_factory=list)  # Most used features
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_analytics"
        indexes = [
            IndexModel([("user_id", 1)], unique=True),
            IndexModel([("last_active", -1)]),
        ]
    
    def __repr__(self):
        return f"<UserAnalytics(user_id='{self.user_id}', sessions={self.total_sessions})>"

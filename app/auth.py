from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings
from .models import User, TokenBlacklist, RefreshToken
from .schemas import TokenData
import uuid
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token():
    """Generate a secure random refresh token"""
    return secrets.token_urlsafe(32)

async def create_refresh_token_record(user_id: str) -> str:
    """Create and store a refresh token in the database"""
    token = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    refresh_token_record = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    await refresh_token_record.save()
    return token

async def verify_refresh_token(token: str) -> Optional[RefreshToken]:
    """Verify and return refresh token if valid"""
    refresh_token = await RefreshToken.find_one(
        RefreshToken.token == token,
        RefreshToken.is_active == True,
        RefreshToken.expires_at > datetime.utcnow()
    )
    return refresh_token

async def revoke_refresh_token(token: str):
    """Revoke a refresh token"""
    refresh_token = await RefreshToken.find_one(RefreshToken.token == token)
    if refresh_token:
        refresh_token.is_active = False
        await refresh_token.save()

async def revoke_all_user_refresh_tokens(user_id: str):
    """Revoke all refresh tokens for a user"""
    await RefreshToken.find(
        RefreshToken.user_id == user_id,
        RefreshToken.is_active == True
    ).update({"$set": {"is_active": False}})

async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted"""
    blacklisted_token = await TokenBlacklist.find_one(TokenBlacklist.token == token)
    return blacklisted_token is not None

async def blacklist_token(token: str, user_id: str):
    """Add a token to the blacklist"""
    try:
        # Decode token to get expiration time
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp_timestamp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        blacklisted_token = TokenBlacklist(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        await blacklisted_token.save()
    except JWTError:
        # If we can't decode the token, still blacklist it with default expiration
        expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        blacklisted_token = TokenBlacklist(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        await blacklisted_token.save()

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    return token_data

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    
    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = verify_token(token, credentials_exception)
    user = await User.find_one(User.user_id == token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

def generate_user_id():
    """Generate a unique user ID"""
    return str(uuid.uuid4())

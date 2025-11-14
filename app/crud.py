from typing import Optional
from .models import User
from .schemas import UserCreate, UserUpdate
from .auth import generate_user_id
from datetime import datetime

async def get_user(user_id: str) -> Optional[User]:
    """Get user by user_id"""
    return await User.find_one(User.user_id == user_id)

async def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email"""
    return await User.find_one(User.email == email)

async def get_user_by_provider_id(provider: str, provider_id: str) -> Optional[User]:
    """Get user by social provider ID"""
    return await User.find_one(
        User.provider == provider,
        User.provider_id == provider_id
    )

async def create_user(user: UserCreate) -> User:
    """Create a new user"""
    user_data = user.dict()
    db_user = User(**user_data)
    await db_user.insert()
    return db_user

async def update_user(user_id: str, user_update: UserUpdate) -> Optional[User]:
    """Update user information"""
    db_user = await get_user(user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if not update_data:
        return db_user
    
    # Check if email is being updated and if it already exists for another user
    if 'email' in update_data and update_data['email']:
        existing_user = await get_user_by_email(update_data['email'])
        if existing_user and existing_user.user_id != user_id:
            raise ValueError("Email already exists for another user")
    
    update_data['updated_at'] = datetime.utcnow()
    await db_user.update({"$set": update_data})
    # Refresh the user object
    db_user = await get_user(user_id)
    
    return db_user

async def delete_user(user_id: str) -> bool:
    """Delete user"""
    db_user = await get_user(user_id)
    if not db_user:
        return False
    
    await db_user.delete()
    return True

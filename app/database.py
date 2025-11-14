from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .config import settings
from .models import User, TokenBlacklist, RefreshToken, Conversation, UserCredits, CreditTransaction, UserAnalytics

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.database_name]
    
    # Initialize beanie with all models
    await init_beanie(database=db.database, document_models=[User, TokenBlacklist, RefreshToken, Conversation, UserCredits, CreditTransaction, UserAnalytics])

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()

# For compatibility with existing code that expects get_db()
async def get_db():
    return db.database

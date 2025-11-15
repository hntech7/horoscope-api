import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, db
from app.routers import auth, users, conversations, credits, analytics

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Horoscope API with Google and Apple social authentication"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track database connection
_db_connected = False

# Database connection middleware for serverless
@app.middleware("http")
async def db_middleware(request, call_next):
    global _db_connected
    if not _db_connected and db.client is None:
        try:
            await connect_to_mongo()
            _db_connected = True
        except Exception as e:
            print(f"Database connection error: {e}")
    response = await call_next(request)
    return response

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(credits.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Horoscope API",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}

# This is the main entry point for Vercel
# Vercel will automatically detect this as the ASGI application

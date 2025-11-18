from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from .config import settings
from .database import connect_to_mongo, close_mongo_connection, db
from .routers import auth, users, conversations, credits, analytics
from .exception_handlers import http_exception_handler, validation_exception_handler, general_exception_handler
from .schemas import StandardResponse
from .response_utils import create_success_response

# Initialize FastAPI app without lifespan for Vercel compatibility
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

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(credits.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

@app.get("/", response_model=StandardResponse[dict])
async def root(response: Response):
    """Root endpoint"""
    return create_success_response(
        response,
        data={
            "version": settings.app_version,
            "docs": "/docs"
        },
        message="Welcome to Horoscope API"
    )

@app.get("/health", response_model=StandardResponse[dict])
async def health_check(response: Response):
    """Health check endpoint"""
    return create_success_response(
        response,
        data={
            "status": "healthy",
            "version": settings.app_version
        },
        message="Service is healthy"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

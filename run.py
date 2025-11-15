#!/usr/bin/env python3
"""
Vercel entry point for Horoscope API
"""

from app.main import app

# Export the app for Vercel
# Vercel will automatically detect this as the ASGI application

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

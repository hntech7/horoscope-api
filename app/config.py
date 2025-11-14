from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "horoscope_db"
    
    # JWT Settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7  # Refresh tokens expire in 7 days
    
    # App Settings
    app_name: str = "Horoscope API"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()

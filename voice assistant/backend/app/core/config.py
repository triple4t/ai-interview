from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Interview Assistant API"
    version: str = "1.0.0"
    debug: bool = False
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database settings - using PostgreSQL
    database_url: str = "postgresql://postgres@localhost:5432/interview_assistant"
    
    # PostgreSQL specific settings
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    
    # CORS settings
    allowed_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Email settings (for future email verification)
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings() 
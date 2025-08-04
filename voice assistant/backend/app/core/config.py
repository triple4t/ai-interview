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
    
    # Database settings
    database_url: str = "sqlite:///./interview_assistant.db"
    
    # CORS settings
    allowed_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Email settings (for future email verification)
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings() 
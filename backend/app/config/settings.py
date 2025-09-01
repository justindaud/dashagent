from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()

# app/config/settings.py
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT"))

    # Database
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = int(os.getenv("DB_PORT"))
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_EXPIRATION_DAYS: int = int(os.getenv("JWT_EXPIRATION_DAYS"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    BCRYPT_COST: int = int(os.getenv("BCRYPT_COST"))
    PASSWORD_PEPPER: str = os.getenv("PASSWORD_PEPPER")
    COOKIE_NAME: str = os.getenv("COOKIE_NAME")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    EXPERIENCE_VS_ID: str = os.getenv("EXPERIENCE_VS_ID")
    GOVERNANCE_VS_ID: str = os.getenv("GOVERNANCE_VS_ID")

    # === Scheduler & Prealloc cleanup ===
    PREALLOC_TTL_MINUTES_UNCONSUMED: int = int(os.getenv("PREALLOC_TTL_MINUTES_UNCONSUMED", "1440"))
    PREALLOC_TTL_MINUTES_CONSUMED: int = int(os.getenv("PREALLOC_TTL_MINUTES_CONSUMED", "4320"))
    PREALLOC_CLEANUP_INTERVAL_MINUTES: int = int(os.getenv("PREALLOC_CLEANUP_INTERVAL_MINUTES", "15"))

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

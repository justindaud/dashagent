# app/config/settings.py
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import Dict, Any, Optional

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

    # Cookies
    COOKIE_NAME: str = os.getenv("COOKIE_NAME")
    COOKIE_DOMAIN: Optional[str] = os.getenv("COOKIE_DOMAIN") or None
    COOKIE_PATH: str = os.getenv("COOKIE_PATH")
    COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE")
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    EXPERIENCE_VS_ID: str = os.getenv("EXPERIENCE_VS_ID")
    GOVERNANCE_VS_ID: str = os.getenv("GOVERNANCE_VS_ID")

    # === ClickHouse config & cleanup ===
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT"))
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD")
    CLICKHOUSE_DB: str = os.getenv("CLICKHOUSE_DB")

    # === Scheduler & Prealloc cleanup ===
    PREALLOC_TTL_MINUTES_UNCONSUMED: int = int(os.getenv("PREALLOC_TTL_MINUTES_UNCONSUMED"))
    PREALLOC_TTL_MINUTES_CONSUMED: int = int(os.getenv("PREALLOC_TTL_MINUTES_CONSUMED"))
    PREALLOC_CLEANUP_INTERVAL_MINUTES: int = int(os.getenv("PREALLOC_CLEANUP_INTERVAL_MINUTES"))
    CSV_CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CSV_CLEANUP_INTERVAL_HOURS"))
    CLICKHOUSE_CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLICKHOUSE_CLEANUP_INTERVAL_HOURS"))

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def clickhouse_url(self) -> str:
        user = self.CLICKHOUSE_USER
        password = self.CLICKHOUSE_PASSWORD
        auth = ""
        if user:
            auth = f"{user}:{password}@"
        return f"clickhouse+http://{auth}{self.CLICKHOUSE_HOST}:{self.CLICKHOUSE_PORT}/{self.CLICKHOUSE_DB}"

    @property
    def clickhouse_base_url(self) -> str:
        return f"http://{self.CLICKHOUSE_HOST}:{self.CLICKHOUSE_PORT}"

    @property
    def clickhouse_default_params(self) -> Dict[str, Any]:
        return {"database": self.CLICKHOUSE_DB}

settings = Settings()

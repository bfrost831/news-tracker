from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost/news_tracker"
    gemini_api_key: str = ""
    news_aggregator_url: str = "http://localhost:8001"
    searxng_url: str = "http://localhost:8888"
    resend_api_key: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_hours: int = 24 * 7  # 7 days
    allowed_origins: List[str] = ["http://localhost:3000", "https://news-tracker.vercel.app"]

    class Config:
        env_file = ".env"


settings = Settings()

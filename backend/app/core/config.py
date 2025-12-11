import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://lensanalytics:lensanalytics_dev@localhost:5432/lensanalytics",
    )

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"

    # Ingestion
    takeout_path: Optional[str] = os.getenv("TAKEOUT_PATH")
    thumbnail_cache: Optional[str] = os.getenv("THUMBNAIL_CACHE", "/mnt/photos/thumbnails")

    # ML Models
    model_path: Optional[str] = os.getenv("MODEL_PATH")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

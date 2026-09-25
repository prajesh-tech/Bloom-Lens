from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application Settings
    APP_NAME: str = "BloomLens V1 Backend"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./bloomlens.db"

    # External AI Services
    GEMINI_API_KEY: Optional[str] = ""

    # Authentication & Security
    API_KEY: Optional[str] = None
    AUTH_ENABLED: bool = False

    # File Storage Settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx"]

    # Hybrid Bloom Classifier Parameters & Weights
    BLOOM_VERIFICATION_THRESHOLD: float = 0.60
    BLOOM_WEIGHT_VERB: float = 0.30
    BLOOM_WEIGHT_SEMANTIC: float = 0.35
    BLOOM_WEIGHT_COGNITIVE: float = 0.25
    BLOOM_WEIGHT_STRUCTURE: float = 0.10

    # Question Similarity Thresholds
    SIMILARITY_THRESHOLD_EXACT: float = 0.95
    SIMILARITY_THRESHOLD_SEMANTIC: float = 0.70
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    WARMUP_EMBEDDING_ON_STARTUP: bool = False

    # OCR Settings
    OCR_LANG: str = "en"

    @property
    def cors_origins(self) -> List[str]:
        """Returns configured frontend origins from comma-separated env config."""
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]

    def validate_runtime_config(self) -> None:
        """Validates runtime settings without exposing secret values."""
        missing = []
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        if self.MAX_UPLOAD_SIZE_MB <= 0:
            missing.append("MAX_UPLOAD_SIZE_MB")

        env = self.APP_ENV.lower()
        key_missing = not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your_gemini_api_key_here"
        if env in {"production", "staging"} and key_missing:
            missing.append("GEMINI_API_KEY")

        if env in {"production", "staging"} and self.AUTH_ENABLED:
            if not self.API_KEY or self.API_KEY.strip() == "":
                missing.append("API_KEY")

        if not self.cors_origins:
            missing.append("FRONTEND_ORIGINS")

        if missing:
            joined = ", ".join(sorted(set(missing)))
            raise RuntimeError(f"Missing or invalid required configuration: {joined}")

    @property
    def sync_database_url(self) -> str:
        """Returns synchronous database URL for Alembic or sync drivers."""
        url = self.DATABASE_URL
        if url.startswith("sqlite+aiosqlite:///"):
            return url.replace("sqlite+aiosqlite:///", "sqlite:///")
        if url.startswith("mysql+aiomysql://"):
            return url.replace("mysql+aiomysql://", "mysql+pymysql://")
        if url.startswith("mysql+asyncmy://"):
            return url.replace("mysql+asyncmy://", "mysql+pymysql://")
        return url


settings = Settings()

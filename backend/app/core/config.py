from typing import List, Optional
from pydantic import model_validator
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

    # Performance Estimation Parameters & Weights
    ESTIMATE_BLOOM_WEIGHT_L1: float = 0.10
    ESTIMATE_BLOOM_WEIGHT_L2: float = 0.25
    ESTIMATE_BLOOM_WEIGHT_L3: float = 0.45
    ESTIMATE_BLOOM_WEIGHT_L4: float = 0.65
    ESTIMATE_BLOOM_WEIGHT_L5: float = 0.85
    ESTIMATE_BLOOM_WEIGHT_L6: float = 1.00

    ESTIMATE_PASS_PCT_INTERCEPT: float = 95.0
    ESTIMATE_PASS_PCT_SLOPE: float = 65.0

    ESTIMATE_AVG_PCT_INTERCEPT: float = 80.0
    ESTIMATE_AVG_PCT_SLOPE: float = 50.0

    ESTIMATE_MAX_EXCLUDED_MARKS_RATIO: float = 0.20

    @model_validator(mode="after")
    def validate_estimate_parameters(self) -> "Settings":
        weights = [
            self.ESTIMATE_BLOOM_WEIGHT_L1,
            self.ESTIMATE_BLOOM_WEIGHT_L2,
            self.ESTIMATE_BLOOM_WEIGHT_L3,
            self.ESTIMATE_BLOOM_WEIGHT_L4,
            self.ESTIMATE_BLOOM_WEIGHT_L5,
            self.ESTIMATE_BLOOM_WEIGHT_L6,
        ]
        for idx, w in enumerate(weights, start=1):
            if not (0.0 <= w <= 1.0):
                raise ValueError(f"ESTIMATE_BLOOM_WEIGHT_L{idx} must be between 0.0 and 1.0, got {w}")
        for i in range(len(weights) - 1):
            if weights[i] > weights[i + 1]:
                raise ValueError(
                    f"Bloom weights must be non-decreasing: L{i+1} ({weights[i]}) > L{i+2} ({weights[i+1]})"
                )
        if not (0.0 <= self.ESTIMATE_MAX_EXCLUDED_MARKS_RATIO <= 1.0):
            raise ValueError(
                f"ESTIMATE_MAX_EXCLUDED_MARKS_RATIO must be between 0.0 and 1.0, got {self.ESTIMATE_MAX_EXCLUDED_MARKS_RATIO}"
            )
        return self

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

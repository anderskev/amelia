"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from pathlib import Path
from enum import Enum
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class Environment(str, Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Application
    APP_NAME: str = "Amelia"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://amelia:amelia@localhost:5432/amelia"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    TEMP_DIR: Path = BASE_DIR / "temp"

    # LLM Providers
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Default LLM Settings
    DEFAULT_MODEL: str = "claude-sonnet-4-5-20250929"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4096

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 200

    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7

    # Claude Code
    CLAUDE_CODE_PATH: str = "claude"
    CLAUDE_CODE_TIMEOUT: int = 300

    # Git
    GIT_WORKTREE_DIR: Path = BASE_DIR / "worktrees"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    # Validators
    @field_validator('ANTHROPIC_API_KEY')
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format."""
        if not v or v == "":
            logger.warning("ANTHROPIC_API_KEY not set - Claude features will be unavailable")
            return v
        if not v.startswith("sk-ant-"):
            raise ValueError("ANTHROPIC_API_KEY must start with 'sk-ant-'")
        return v

    @field_validator('OPENROUTER_API_KEY')
    @classmethod
    def validate_openrouter_key(cls, v: str) -> str:
        """Validate OpenRouter API key format."""
        if v and not v.startswith("sk-or-"):
            logger.warning("OPENROUTER_API_KEY should start with 'sk-or-'")
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate PostgreSQL connection string."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator('CHUNK_SIZE')
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is reasonable."""
        if v < 100:
            raise ValueError("CHUNK_SIZE too small - minimum 100 characters")
        if v > 4000:
            logger.warning(f"CHUNK_SIZE {v} is very large - may exceed model context limits")
        return v

    @model_validator(mode='after')
    def validate_chunk_overlap(self):
        """Validate chunk overlap is less than chunk size."""
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        return self

    @model_validator(mode='after')
    def validate_pool_settings(self):
        """Validate database pool configuration."""
        if self.DATABASE_POOL_SIZE < 1:
            raise ValueError("DATABASE_POOL_SIZE must be at least 1")
        if self.DATABASE_MAX_OVERFLOW < 0:
            raise ValueError("DATABASE_MAX_OVERFLOW cannot be negative")
        return self

    # Environment helper properties
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.ENVIRONMENT == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.GIT_WORKTREE_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

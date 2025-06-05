import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_name: str = "Gestione Palchi API"
    app_version: str = "1.0.0"
    app_port: int = Field(default=8000, description="Application port")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(
        default="production", description="Application environment"
    )

    # Database settings
    database_url: str = Field(
        default="sqlite:///./gestione_palchi.db", description="Database connection URL"
    )
    database_echo: bool = Field(
        default=False, description="Enable SQLAlchemy query logging"
    )

    # Authentication settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 30 * 12, description="Access token expiration time in minutes"
    )

    # API settings
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    max_connections_count: int = Field(
        default=10, description="Maximum database connections"
    )
    min_connections_count: int = Field(
        default=10, description="Minimum database connections"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for SQLAlchemy."""
        if self.database_url.startswith("sqlite"):
            return self.database_url
        return self.database_url.replace("postgresql://", "postgresql+psycopg2://")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return not self.debug and self.environment == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings instance."""
    return settings

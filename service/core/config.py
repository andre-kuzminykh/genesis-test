"""
Application settings from environment.

## Traceability
Feature: F001-F009 — All features
"""
import os


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_NAME: str = os.getenv("DB_NAME", "product_engineer")
    DB_URL: str = os.getenv("DATABASE_URL", "")
    API_V1_PREFIX: str = "/api/v1"

    @property
    def database_url(self) -> str:
        if self.DB_URL:
            return self.DB_URL
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


config = Settings()

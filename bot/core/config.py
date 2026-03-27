"""Application settings loaded from environment variables.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    """Bot configuration sourced from env / .env file."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))


config = Settings()

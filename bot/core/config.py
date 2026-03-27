"""Application settings loaded from environment variables.

## Traceability
Product: Telegram Product Engineer Bot
"""
import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    """Bot configuration sourced from env / .env file."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")


config = Settings()

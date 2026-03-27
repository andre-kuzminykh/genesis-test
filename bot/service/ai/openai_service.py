"""OpenAI GPT service for product engineering assistance.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

from openai import AsyncOpenAI

from core.config import config

SYSTEM_PROMPT = (
    "You are a Product Engineering assistant inside a Telegram bot.\n"
    "You help users design products, write features, user stories, "
    "acceptance criteria, flows, use cases, and requirements.\n"
    "Be concise — Telegram messages have a 4096-char limit.\n"
    "Format with Markdown where appropriate.\n"
    "Answer in the user's language."
)


class OpenAIService:
    """Thin async wrapper around the OpenAI chat completions API."""

    def __init__(self):
        self._client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self._model = config.OPENAI_MODEL
        self._max_tokens = config.OPENAI_MAX_TOKENS

    async def chat(
        self,
        user_message: str,
        history: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Send a message to GPT and return the assistant reply."""
        messages = [
            {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    async def generate_product_spec(self, product_name: str, description: str) -> str:
        """Generate goal, value proposition, constraints for a product."""
        prompt = (
            f"Product name: {product_name}\n"
            f"Description: {description}\n\n"
            "Generate a short product specification with:\n"
            "1. Goal (1-2 sentences)\n"
            "2. Value proposition (1-2 sentences)\n"
            "3. Target users (bullet list)\n"
            "4. Key constraints (bullet list)\n"
            "Be concise."
        )
        return await self.chat(prompt)

    async def generate_features(self, product_name: str, goal: str) -> str:
        """Suggest features for a product."""
        prompt = (
            f"Product: {product_name}\n"
            f"Goal: {goal}\n\n"
            "Suggest 5-7 features as a numbered list. "
            "Each feature: short name + one-sentence description."
        )
        return await self.chat(prompt)

    async def generate_user_stories(self, feature_name: str, actor: str) -> str:
        """Generate user stories for a feature."""
        prompt = (
            f"Feature: {feature_name}\n"
            f"Actor: {actor}\n\n"
            "Write 3-5 user stories in format:\n"
            "As a {actor}, I want {action} so that {benefit}."
        )
        return await self.chat(prompt)

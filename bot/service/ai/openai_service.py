"""OpenAI GPT service for product engineering assistance.

## Traceability
Product: Telegram Product Engineer Bot
"""
from __future__ import annotations

import json
import tempfile
import os

from openai import AsyncOpenAI

from core.config import config

SYSTEM_PROMPT = (
    "You are a Product Engineering assistant inside a Telegram bot.\n"
    "You help users design products, write features, user stories, "
    "acceptance criteria, flows, use cases, and requirements.\n"
    "Be concise — Telegram messages have a 4096-char limit.\n"
    "Answer in the user's language.\n"
    "IMPORTANT: NEVER use markdown formatting like **bold** or *italic*. "
    "Use plain text only. No asterisks for emphasis."
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

    async def transcribe_voice(self, file_path: str) -> str:
        """Transcribe a voice/audio file using Whisper."""
        with open(file_path, "rb") as f:
            transcript = await self._client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        return transcript.text

    async def generate_product_summary(self, name: str, description: str) -> str:
        prompt = (
            f"Product: {name}\n"
            f"Description: {description}\n\n"
            "Write a concise product summary in the following structure:\n"
            "1. Client — who is the target audience (1-2 sentences)\n"
            "2. Problem — what pain point they have (1-2 sentences)\n"
            "3. Solution — how this product solves it (2-3 sentences)\n"
            "4. Key metrics — 3-5 measurable success metrics\n\n"
            "Be brief. Use plain text only, NO markdown, NO asterisks."
        )
        return await self.chat(prompt)

    async def generate_features_json(self, product_name: str, summary: str) -> list[dict]:
        """Return list of features as structured data."""
        prompt = (
            f"Product: {product_name}\n"
            f"Summary: {summary}\n\n"
            "Generate 5-7 features. Return ONLY valid JSON array:\n"
            '[{"name": "Feature Name", "description": "One sentence description"}]\n'
            "No markdown, no explanation — pure JSON array only."
        )
        raw = await self.chat(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)

    async def generate_stories_json(self, feature_name: str, feature_desc: str) -> list[dict]:
        """Return user stories as structured data."""
        prompt = (
            f"Feature: {feature_name}\n"
            f"Description: {feature_desc}\n\n"
            "Generate 3-5 user stories. Return ONLY valid JSON array:\n"
            '[{"title": "Short title", "actor": "User", '
            '"want": "what they want", "benefit": "why"}]\n'
            "No markdown — pure JSON array only."
        )
        raw = await self.chat(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)

    async def generate_flows_json(self, story_title: str) -> list[dict]:
        """Return flows as structured data."""
        prompt = (
            f"User Story: {story_title}\n\n"
            "Generate 1-3 user flows (primary + alternatives). "
            "Return ONLY valid JSON array:\n"
            '[{"title": "Flow title", "flow_type": "primary", '
            '"description": "Brief description", '
            '"mermaid_source": "graph TD\\n    A[Start] --> B[Step] --> C[End]"}]\n'
            "No markdown — pure JSON array only."
        )
        raw = await self.chat(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)

    async def edit_text(self, original: str, user_instruction: str) -> str:
        """Apply user's edit instruction to existing text."""
        prompt = (
            f"Original text:\n{original}\n\n"
            f"User's edit instruction: {user_instruction}\n\n"
            "Return the corrected/updated text. Keep the same structure.\n"
            "Use plain text only, NO markdown, NO asterisks."
        )
        return await self.chat(prompt)

    async def edit_features_list(self, current_list: str,
                                 user_instruction: str) -> list[dict]:
        """Edit a feature list based on user instruction. Return JSON array."""
        prompt = (
            f"Current feature list:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Apply the user's changes to the feature list.\n"
            "Return ONLY a valid JSON array:\n"
            '[{"name": "Feature Name", "description": "Description"}]\n'
            "No markdown, no explanation — pure JSON array only."
        )
        raw = await self.chat(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)

    async def edit_stories_list(self, current_list: str,
                                user_instruction: str) -> list[dict]:
        """Edit a stories list based on user instruction. Return JSON array."""
        prompt = (
            f"Current stories list:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Apply the user's changes to the stories list.\n"
            "Return ONLY a valid JSON array:\n"
            '[{"title": "Title", "want": "what user wants", "benefit": "why"}]\n'
            "No markdown, no explanation — pure JSON array only."
        )
        raw = await self.chat(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)

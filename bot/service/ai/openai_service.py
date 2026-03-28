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


def _strip_json(raw: str) -> str:
    """Strip markdown code fences from JSON response."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return raw


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
        with open(file_path, "rb") as f:
            transcript = await self._client.audio.transcriptions.create(
                model="whisper-1", file=f,
            )
        return transcript.text

    # ─── Product ────────────────────────────────────────────

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

    # ─── Features ───────────────────────────────────────────

    async def generate_features_json(self, product_name: str, summary: str) -> list[dict]:
        prompt = (
            f"Product: {product_name}\nSummary: {summary}\n\n"
            "Generate 5-7 features. Return ONLY valid JSON array:\n"
            '[{"name": "Feature Name", "description": "One sentence description"}]\n'
            "No markdown, no explanation — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    async def edit_features_list(self, current_list: str,
                                 user_instruction: str) -> list[dict]:
        prompt = (
            f"Current feature list:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Apply the user's changes to the feature list.\n"
            "Return ONLY a valid JSON array:\n"
            '[{"name": "Feature Name", "description": "Description"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    # ─── Roles / Actors ─────────────────────────────────────

    async def generate_roles_json(self, feature_name: str,
                                  feature_desc: str) -> list[dict]:
        prompt = (
            f"Feature: {feature_name}\nDescription: {feature_desc}\n\n"
            "Generate 2-5 human user roles who use this feature.\n"
            "Only real people who interact with the system — "
            "NO systems, services, APIs or external integrations.\n"
            "Examples: end user, admin, manager, moderator, support agent.\n"
            "Return ONLY valid JSON array:\n"
            '[{"name": "Role Name", "description": "Who this person is"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    async def edit_roles_list(self, current_list: str,
                              user_instruction: str) -> list[dict]:
        prompt = (
            f"Current roles:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Only human user roles — no systems or services.\n"
            "Return ONLY a valid JSON array:\n"
            '[{"name": "Role Name", "description": "Who this person is"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    # ─── Stories ────────────────────────────────────────────

    async def generate_stories_json(self, feature_name: str,
                                    feature_desc: str,
                                    role_name: str = "") -> list[dict]:
        role_ctx = f"\nRole/Actor: {role_name}\n" if role_name else ""
        prompt = (
            f"Feature: {feature_name}\nDescription: {feature_desc}\n"
            f"{role_ctx}\n"
            "Generate 3-5 user stories from this role's perspective. "
            "Return ONLY valid JSON array:\n"
            '[{"title": "Short title", "want": "what they want", "benefit": "why"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    async def edit_stories_list(self, current_list: str,
                                user_instruction: str) -> list[dict]:
        prompt = (
            f"Current stories:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Return ONLY a valid JSON array:\n"
            '[{"title": "Title", "want": "what user wants", "benefit": "why"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    # ─── Flows (with mermaid sequence) ──────────────────────

    async def generate_flows_json(self, story_title: str,
                                  story_want: str = "",
                                  roles: str = "") -> list[dict]:
        prompt = (
            f"User Story: {story_title}\n"
            f"Want: {story_want}\n"
            f"Actors/Roles: {roles}\n\n"
            "Generate 1-3 user flows (primary + alternatives).\n"
            "For each flow generate a Mermaid sequence diagram showing "
            "interactions between actors (roles) and systems.\n"
            "Return ONLY valid JSON array:\n"
            '[{"title": "Flow title", "flow_type": "primary", '
            '"description": "Step-by-step flow description", '
            '"mermaid_source": "sequenceDiagram\\n    Actor->>System: action\\n    ..."}]\n'
            "IMPORTANT: mermaid_source must be valid Mermaid sequenceDiagram syntax.\n"
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    async def edit_flows_list(self, current_list: str,
                              user_instruction: str) -> list[dict]:
        prompt = (
            f"Current flows:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Return ONLY a valid JSON array:\n"
            '[{"title": "Title", "flow_type": "primary", '
            '"description": "...", "mermaid_source": "sequenceDiagram\\n..."}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    # ─── Use Cases (Given/When/Then) ────────────────────────

    async def generate_use_cases_json(self, story_title: str,
                                      flow_titles: str) -> list[dict]:
        prompt = (
            f"User Story: {story_title}\n"
            f"Flows: {flow_titles}\n\n"
            "Generate 2-4 use cases derived from the user flows above.\n"
            "Each use case must logically follow from the flows.\n"
            "Use Given/When/Then format.\n"
            "Return ONLY valid JSON array:\n"
            '[{"title": "UC title", "goal": "Goal", '
            '"given_text": "Given...", "when_text": "When...", '
            '"then_text": "Then..."}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    async def edit_use_cases_list(self, current_list: str,
                                  user_instruction: str) -> list[dict]:
        prompt = (
            f"Current use cases:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Return ONLY a valid JSON array:\n"
            '[{"title": "Title", "goal": "Goal", '
            '"given_text": "Given...", "when_text": "When...", '
            '"then_text": "Then..."}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    # ─── Requirements (functional / non-functional) ─────────

    async def generate_requirements_json(self, use_case_title: str,
                                         use_case_goal: str = "",
                                         given_when_then: str = "") -> list[dict]:
        prompt = (
            f"Use Case: {use_case_title}\n"
            f"Goal: {use_case_goal}\n"
            f"Scenario: {given_when_then}\n\n"
            "Decompose this use case into specific requirements.\n"
            "Include both functional and non-functional requirements.\n"
            "Return ONLY valid JSON array:\n"
            '[{"title": "Requirement title", "text": "Detailed description", '
            '"requirement_type": "functional|non-functional", '
            '"priority": "high|medium|low"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    async def edit_requirements_list(self, current_list: str,
                                     user_instruction: str) -> list[dict]:
        prompt = (
            f"Current requirements:\n{current_list}\n\n"
            f"User's instruction: {user_instruction}\n\n"
            "Return ONLY a valid JSON array:\n"
            '[{"title": "Title", "text": "Description", '
            '"requirement_type": "functional|non-functional", '
            '"priority": "high|medium|low"}]\n'
            "No markdown — pure JSON array only."
        )
        return json.loads(_strip_json(await self.chat(prompt)))

    # ─── Generic ────────────────────────────────────────────

    async def edit_text(self, original: str, user_instruction: str) -> str:
        prompt = (
            f"Original text:\n{original}\n\n"
            f"User's edit instruction: {user_instruction}\n\n"
            "Return the corrected/updated text. Keep the same structure.\n"
            "Use plain text only, NO markdown, NO asterisks."
        )
        return await self.chat(prompt)

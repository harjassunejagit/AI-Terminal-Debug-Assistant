from __future__ import annotations

import json
import re
from typing import Optional
from src.core.config import Config


SYSTEM_PROMPT = """You are DebugAI — a senior software engineer and debugging expert.

When given an error message and parsed metadata, you:

1. Explain clearly what went wrong (in plain English, 2-4 sentences)
2. Identify the root cause precisely
3. Suggest 1-3 actionable fix commands
4. Give a brief prevention tip

ALWAYS respond with valid JSON in exactly this structure:

{
  "explanation": "...",
  "root_cause": "...",
  "fix_commands": [
    {"command": "...", "explanation": "..."}
  ],
  "prevention": "...",
  "references": [
    {"title": "...", "url": "..."}
  ]
}

No markdown, only raw JSON.
"""


def _build_user_message(error_text: str, parsed: dict) -> str:
    return f"""Error:
{error_text.strip()[:2000]}

Language: {parsed.get("language", "Unknown")}
Error Type: {parsed.get("error_type", "Unknown")}
File: {parsed.get("file", "N/A")}
Line: {parsed.get("line", "N/A")}
Severity: {parsed.get("severity", "medium")}
Message: {parsed.get("message", "")}

Return JSON only."""


def _parse_llm_response(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass

        return {
            "explanation": raw,
            "root_cause": "Parse failure",
            "fix_commands": [],
            "prevention": "",
            "references": [],
        }


class LLMClient:
    def __init__(self, config: Config):
        self.config = config

    def analyze(self, error_text: str, parsed: dict) -> dict:
        provider = (self.config.provider or "").lower()

        if provider == "openai":
            return self._call_openai(error_text, parsed)

        if provider == "ollama":
            return self._call_ollama(error_text, parsed)

        if provider == "anthropic":
            return self._call_anthropic(error_text, parsed)

        if provider == "gemini":
            return self._call_gemini(error_text, parsed)

        raise ValueError(f"Unknown provider: {provider}")

    def _call_openai(self, error_text: str, parsed: dict) -> dict:
        from openai import OpenAI

        if not self.config.openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY")

        client = OpenAI(api_key=self.config.openai_api_key)

        resp = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(error_text, parsed)},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        return _parse_llm_response(resp.choices[0].message.content)

    def _call_ollama(self, error_text: str, parsed: dict) -> dict:
        import httpx

        url = f"{self.config.ollama_base_url}/api/chat"

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(error_text, parsed)},
            ],
            "stream": False,
        }

        with httpx.Client(timeout=60) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return _parse_llm_response(resp.json()["message"]["content"])

    def _call_anthropic(self, error_text: str, parsed: dict) -> dict:
        import anthropic

        if not self.config.anthropic_api_key:
            raise ValueError("Missing ANTHROPIC_API_KEY")

        client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)

        msg = client.messages.create(
            model=self.config.model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_message(error_text, parsed)},
            ],
        )

        return _parse_llm_response(msg.content[0].text)

    def _call_gemini(self, error_text: str, parsed: dict) -> dict:
        from google import genai

        if not self.config.gemini_api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        client = genai.Client(api_key=self.config.gemini_api_key)

        prompt = f"""{SYSTEM_PROMPT}

{_build_user_message(error_text, parsed)}"""

        resp = client.models.generate_content(
            model=self.config.model,
            contents=prompt,
        )

        return _parse_llm_response(resp.text)
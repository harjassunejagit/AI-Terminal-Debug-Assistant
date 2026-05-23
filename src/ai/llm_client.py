"""
LLM Client — unified interface for OpenAI, Ollama, and Anthropic.
Returns structured analysis dicts.
"""

from __future__ import annotations

import json
import re
from typing import Optional
from src.core.config import Config


SYSTEM_PROMPT = """You are DebugAI — a senior software engineer and debugging expert.
When given an error message and parsed metadata, you:
1. Explain clearly what went wrong (in plain English, 2-4 sentences)
2. Identify the root cause precisely
3. Suggest 1-3 actionable fix commands (e.g. pip install X, export VAR=val, etc.)
4. Give a brief prevention tip

ALWAYS respond with valid JSON in exactly this structure:
{
  "explanation": "...",
  "root_cause": "...",
  "fix_commands": [
    {"command": "pip install python-dotenv", "explanation": "Installs the missing dotenv library"},
    ...
  ],
  "prevention": "...",
  "references": [
    {"title": "Python dotenv docs", "url": "https://pypi.org/project/python-dotenv/"}
  ]
}

Be concise, specific, and actionable. No markdown fences, just raw JSON."""


def _build_user_message(error_text: str, parsed: dict) -> str:
    return f"""Error to debug:
```
{error_text.strip()[:2000]}
```

Parsed metadata:
- Language: {parsed.get("language", "Unknown")}
- Error Type: {parsed.get("error_type", "Unknown")}
- File: {parsed.get("file", "N/A")}
- Line: {parsed.get("line", "N/A")}
- Severity: {parsed.get("severity", "medium")}
- Message: {parsed.get("message", "")}

Analyze and respond with JSON only."""


def _parse_llm_response(raw: str) -> dict:
    """Extract JSON from LLM response, stripping any markdown fences."""
    raw = raw.strip()
    # Strip ```json ... ``` fences
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: try to find JSON object
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
        return {
            "explanation": raw,
            "root_cause": "Unable to parse structured response.",
            "fix_commands": [],
            "prevention": "",
            "references": [],
        }


class LLMClient:
    def __init__(self, config: Config):
        self.config = config

    def analyze(self, error_text: str, parsed: dict) -> dict:
        provider = self.config.provider.lower()
        if provider == "openai":
            return self._call_openai(error_text, parsed)
        elif provider == "ollama":
            return self._call_ollama(error_text, parsed)
        elif provider == "anthropic":
            return self._call_anthropic(error_text, parsed)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    # ── OpenAI ──────────────────────────────────────────────────────────────

    def _call_openai(self, error_text: str, parsed: dict) -> dict:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run: pip install openai")

        if not self.config.openai_api_key:
            raise ValueError("Set OPENAI_API_KEY or run 'debugai config-init'")

        client = OpenAI(api_key=self.config.openai_api_key)
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(error_text, parsed)},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return _parse_llm_response(response.choices[0].message.content)

    # ── Ollama ───────────────────────────────────────────────────────────────

    def _call_ollama(self, error_text: str, parsed: dict) -> dict:
        try:
            import httpx
        except ImportError:
            raise ImportError("Run: pip install httpx")

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(error_text, parsed)},
            ],
            "stream": False,
        }
        url = f"{self.config.ollama_base_url}/api/chat"
        with httpx.Client(timeout=60) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return _parse_llm_response(data["message"]["content"])

    # ── Anthropic ────────────────────────────────────────────────────────────

    def _call_anthropic(self, error_text: str, parsed: dict) -> dict:
        try:
            import anthropic
        except ImportError:
            raise ImportError("Run: pip install anthropic")

        if not self.config.anthropic_api_key:
            raise ValueError("Set ANTHROPIC_API_KEY or run 'debugai config-init'")

        client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        message = client.messages.create(
            model=self.config.model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_user_message(error_text, parsed)},
            ],
        )
        return _parse_llm_response(message.content[0].text)

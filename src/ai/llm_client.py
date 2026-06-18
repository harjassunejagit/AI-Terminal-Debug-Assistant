from __future__ import annotations

import json
import re
import time
import httpx

from src.core.config import Config


SYSTEM_PROMPT = """
You are DebugAI — a senior software engineer and debugging expert.

Return ONLY valid JSON:

{
  "explanation": "",
  "root_cause": "",
  "fix_commands": [
    {
      "command": "",
      "explanation": ""
    }
  ],
  "prevention": "",
  "references": [
    {
      "title": "",
      "url": ""
    }
  ]
}
"""


def _build_user_message(error_text: str, parsed: dict) -> str:
    return f"""
Error:
{error_text.strip()[:2000]}

Language: {parsed.get("language", "Unknown")}
Error Type: {parsed.get("error_type", "Unknown")}
File: {parsed.get("file", "N/A")}
Line: {parsed.get("line", "N/A")}
Severity: {parsed.get("severity", "medium")}
Message: {parsed.get("message", "")}

Return JSON only.
"""


def _parse(raw: str) -> dict:
    raw = raw.strip()

    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)

    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())

            except Exception:
                pass

    return {
        "explanation": raw,
        "root_cause": "Response parsing failed",
        "fix_commands": [],
        "prevention": "",
        "references": [],
    }


class LLMClient:

    def __init__(self, config: Config):
        self.config = config

    def analyze(self, error_text: str, parsed: dict) -> dict:

        provider = self.config.provider.lower()

        if provider == "gemini":
            return self._gemini(error_text, parsed)

        if provider == "openai":
            return self._openai(error_text, parsed)

        if provider == "ollama":
            return self._ollama(error_text, parsed)

        if provider == "anthropic":
            return self._anthropic(error_text, parsed)

        raise ValueError(f"Unknown provider: {provider}")

    def _gemini(self, error_text: str, parsed: dict) -> dict:

        from google import genai

        if not self.config.gemini_api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY\n"
                "Run:\n"
                "setx GEMINI_API_KEY \"YOUR_KEY\""
            )

        client = genai.Client(
            api_key=self.config.gemini_api_key
        )

        prompt = (
            SYSTEM_PROMPT
            + "\n\n"
            + _build_user_message(error_text, parsed)
        )

        models = [
            self.config.model,
            "gemini-2.5-flash-lite",
            "gemini-1.5-flash",
        ]

        last_error = None

        for model in models:

            for attempt in range(3):

                try:

                    print(f"\n[DEBUG] Trying model: {model}")

                    resp = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )

                    return _parse(resp.text)

                except Exception as e:

                    last_error = str(e)

                    print(
                        f"[Retry {attempt + 1}/3] {e}"
                    )

                    time.sleep(3)

        return {
            "explanation":
                "AI service unavailable right now.",
            "root_cause":
                last_error,
            "fix_commands": [
                {
                    "command":
                        "Retry after 30 seconds",
                    "explanation":
                        "Gemini servers overloaded"
                }
            ],
            "prevention":
                "Use fallback models and retries.",
            "references": [],
        }

    def _openai(self, error_text: str, parsed: dict):

        from openai import OpenAI

        if not self.config.openai_api_key:
            raise ValueError("Missing OPENAI_API_KEY")

        client = OpenAI(
            api_key=self.config.openai_api_key
        )

        resp = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content":
                    _build_user_message(
                        error_text,
                        parsed
                    )
                }
            ],
        )

        return _parse(
            resp.choices[0].message.content
        )

    def _ollama(self, error_text: str, parsed: dict):

        url = (
            f"{self.config.ollama_base_url}"
            "/api/chat"
        )

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content":
                    _build_user_message(
                        error_text,
                        parsed
                    )
                }
            ],
            "stream": False,
        }

        with httpx.Client(timeout=60) as client:

            resp = client.post(
                url,
                json=payload
            )

            resp.raise_for_status()

            return _parse(
                resp.json()["message"]["content"]
            )

    def _anthropic(self, error_text: str, parsed: dict):

        import anthropic

        if not self.config.anthropic_api_key:
            raise ValueError(
                "Missing ANTHROPIC_API_KEY"
            )

        client = anthropic.Anthropic(
            api_key=self.config.anthropic_api_key
        )

        resp = client.messages.create(
            model=self.config.model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content":
                    _build_user_message(
                        error_text,
                        parsed
                    )
                }
            ]
        )

        return _parse(
            resp.content[0].text
        )
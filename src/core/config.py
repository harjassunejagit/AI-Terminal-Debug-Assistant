"""
Configuration management — reads ~/.debugai/config.yaml and env vars.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

CONFIG_DIR = Path.home() / ".debugai"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "provider": "gemini",
    "model": "gemini-1.5-flash",
    "ollama_base_url": "http://localhost:11434",
    "max_history": 50,
    "verbose": False,
    "auto_fix": False,
    "theme": "dark",
}


class Config:
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        verbose: bool = False,
        auto_fix: bool = False,
    ):
        file_cfg = self._load_file()

        # Merge: CLI args > env vars > config file > defaults
        self.provider = provider or os.getenv("DEBUGAI_PROVIDER") or file_cfg.get("provider") or DEFAULTS["provider"]
        self.model = model or os.getenv("DEBUGAI_MODEL") or file_cfg.get("model") or DEFAULTS["model"]
        self.verbose = verbose or file_cfg.get("verbose", DEFAULTS["verbose"])
        self.auto_fix = auto_fix or file_cfg.get("auto_fix", DEFAULTS["auto_fix"])
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL") or file_cfg.get("ollama_base_url") or DEFAULTS["ollama_base_url"]
        self.max_history = file_cfg.get("max_history", DEFAULTS["max_history"])

        # API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or file_cfg.get("openai_api_key")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or file_cfg.get("anthropic_api_key")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or file_cfg.get("gemini_api_key")

    def _load_file(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

    @classmethod
    def init_interactive(cls):
        """Interactive setup wizard."""
        console.print("\n[bold cyan]🛠 DebugAI Setup Wizard[/bold cyan]\n")

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        provider = Prompt.ask(
            "AI Provider",
            choices=["gemini", "openai", "ollama", "anthropic"],
            default="gemini",
        )

        model_defaults = {
            "gemini": "gemini-1.5-flash",
            "openai": "gpt-4o-mini",
            "ollama": "llama3",
            "anthropic": "claude-3-haiku-20240307",
        }
        model = Prompt.ask("Model name", default=model_defaults[provider])

        cfg: dict = {"provider": provider, "model": model}

        if provider == "gemini":
            console.print("\n[dim]Get a FREE Gemini API key at: https://aistudio.google.com/apikey[/dim]")
            key = Prompt.ask("Gemini API Key", password=True, default="")
            if key:
                cfg["gemini_api_key"] = key

        elif provider == "openai":
            key = Prompt.ask("OpenAI API Key (leave blank to use env var OPENAI_API_KEY)", password=True, default="")
            if key:
                cfg["openai_api_key"] = key

        elif provider == "anthropic":
            key = Prompt.ask("Anthropic API Key (leave blank to use env var)", password=True, default="")
            if key:
                cfg["anthropic_api_key"] = key

        elif provider == "ollama":
            url = Prompt.ask("Ollama base URL", default="http://localhost:11434")
            cfg["ollama_base_url"] = url

        cfg["verbose"] = Confirm.ask("Enable verbose output by default?", default=False)
        cfg["auto_fix"] = Confirm.ask("Enable auto-fix for safe commands by default?", default=False)

        with open(CONFIG_FILE, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)

        console.print(f"\n[green]✓ Config saved to {CONFIG_FILE}[/green]")
        console.print("\nYou're all set! Try:\n  [cyan]debugai run \"python app.py\"[/cyan]\n")
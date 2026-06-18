from __future__ import annotations

import os
import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

CONFIG_DIR = Path.home() / ".debugai"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "ollama_base_url": "http://localhost:11434",
    "max_history": 50,
    "verbose": False,
    "auto_fix": False,
    "theme": "dark",
}


class Config:

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        verbose: bool | None = None,
        auto_fix: bool | None = None,
    ):

        file_cfg = self._load_file()

        self.provider = (
            provider
            or os.getenv("DEBUGAI_PROVIDER")
            or file_cfg.get("provider")
            or DEFAULTS["provider"]
        ).lower()

        self.model = (
            model
            or os.getenv("DEBUGAI_MODEL")
            or file_cfg.get("model")
            or DEFAULTS["model"]
        )

        if self.provider == "gemini":
            invalid = [
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
            ]

            if self.model in invalid:
                self.model = "gemini-2.5-flash"

        self.verbose = (
            file_cfg.get("verbose", DEFAULTS["verbose"])
            if verbose is None
            else verbose
        )

        self.auto_fix = (
            file_cfg.get("auto_fix", DEFAULTS["auto_fix"])
            if auto_fix is None
            else auto_fix
        )

        self.ollama_base_url = (
            os.getenv("OLLAMA_BASE_URL")
            or file_cfg.get("ollama_base_url")
            or DEFAULTS["ollama_base_url"]
        )

        self.max_history = (
            file_cfg.get("max_history", DEFAULTS["max_history"])
        )

        self.openai_api_key = (
            os.getenv("OPENAI_API_KEY")
            or file_cfg.get("openai_api_key")
        )

        self.anthropic_api_key = (
            os.getenv("ANTHROPIC_API_KEY")
            or file_cfg.get("anthropic_api_key")
        )

        self.gemini_api_key = (
            os.getenv("GEMINI_API_KEY")
            or file_cfg.get("gemini_api_key")
        )

    def _load_file(self):

        if not CONFIG_FILE.exists():
            return {}

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}

        except Exception:
            return {}

    @classmethod
    def init_interactive(cls):

        console.print("\n🛠 DebugAI Setup Wizard\n")

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        provider = Prompt.ask(
            "AI Provider",
            choices=[
                "gemini",
                "openai",
                "ollama",
                "anthropic",
            ],
            default="gemini",
        )

        model_defaults = {
            "gemini": "gemini-2.5-flash",
            "openai": "gpt-4o-mini",
            "ollama": "llama3",
            "anthropic": "claude-3-haiku-20240307",
        }

        model = Prompt.ask(
            "Model name",
            default=model_defaults[provider],
        )

        cfg = {
            "provider": provider,
            "model": model,
        }

        if provider == "gemini":

            console.print(
                "\nGet Gemini API key:\n"
                "https://aistudio.google.com/apikey\n"
            )

            key = Prompt.ask(
                "Gemini API Key",
                password=True,
                default="",
            )

            if key:
                cfg["gemini_api_key"] = key

        elif provider == "openai":

            key = Prompt.ask(
                "OpenAI API Key",
                password=True,
                default="",
            )

            if key:
                cfg["openai_api_key"] = key

        elif provider == "anthropic":

            key = Prompt.ask(
                "Anthropic API Key",
                password=True,
                default="",
            )

            if key:
                cfg["anthropic_api_key"] = key

        elif provider == "ollama":

            cfg["ollama_base_url"] = Prompt.ask(
                "Ollama base URL",
                default="http://localhost:11434",
            )

        cfg["verbose"] = Confirm.ask(
            "Enable verbose output?",
            default=False,
        )

        cfg["auto_fix"] = Confirm.ask(
            "Enable auto-fix?",
            default=False,
        )

        with open(
            CONFIG_FILE,
            "w",
            encoding="utf-8",
        ) as f:
            yaml.dump(
                cfg,
                f,
                default_flow_style=False,
            )

        console.print(
            f"\n✓ Saved to {CONFIG_FILE}\n"
        )

        console.print(
            "Run:\n"
            "python -m src.cli.main explain "
            "\"ZeroDivisionError\"\n"
        )


if __name__ == "__main__":

    cfg = Config()

    print("MAIN BLOCK STARTED")
    print("PROVIDER:", cfg.provider)
    print("MODEL:", cfg.model)
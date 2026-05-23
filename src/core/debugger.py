"""
Core Debug Session — orchestrates parsing, AI analysis, and output rendering.
"""

from __future__ import annotations

import time
import subprocess
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich import box

from src.parsers.error_parser import ErrorParser
from src.ai.llm_client import LLMClient
from src.core.history import DebugHistory
from src.core.config import Config

console = Console()


class DebugSession:

    def __init__(self, config: Config):
        self.config = config
        self.parser = ErrorParser()
        self.llm = LLMClient(config)
        self.history = DebugHistory()

    def analyze(self, error_text: str, auto_fix: bool = False):
        parsed = self.parser.parse(error_text)

        if self.config.verbose:
            self._show_parsed_info(parsed)

        self._show_classification(parsed)

        console.print("\n[bold cyan]🤖 Analyzing with AI...[/bold cyan]")

        with Live(Spinner("dots", text="[cyan]Thinking...[/cyan]"), refresh_per_second=10):
            start = time.time()
            response = self.llm.analyze(error_text, parsed)
            elapsed = time.time() - start

        console.print(f"[dim]Analysis completed in {elapsed:.1f}s[/dim]\n")

        self._render_analysis(response)

        if auto_fix:
            self._apply_fixes(response.get("fix_commands", []))

        self.history.save(error_text, parsed, response)

    def _show_classification(self, parsed: dict):
        table = Table(box=box.ROUNDED, show_header=False, border_style="dim")
        table.add_column("Key", style="bold cyan", width=18)
        table.add_column("Value", style="white")

        table.add_row("Error Type", f"[red]{parsed.get('error_type', 'Unknown')}[/red]")
        table.add_row("Language", parsed.get("language", "Unknown"))
        table.add_row("Severity", self._severity_badge(parsed.get("severity", "medium")))

        if parsed.get("file"):
            table.add_row("File", parsed["file"])
        if parsed.get("line"):
            table.add_row("Line", str(parsed["line"]))

        console.print(table)

    def _severity_badge(self, severity: str) -> str:
        colors = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "critical": "bold red",
        }
        color = colors.get(severity, "white")
        return f"[{color}]{severity.upper()}[/{color}]"

    def _render_analysis(self, response: dict):

        if response.get("explanation"):
            console.print(
                Panel(
                    Markdown(response["explanation"]),
                    title="[bold yellow]📖 What happened[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                )
            )

        if response.get("root_cause"):
            console.print(
                Panel(
                    response["root_cause"],
                    title="[bold red]🔍 Root Cause[/bold red]",
                    border_style="red",
                    padding=(0, 2),
                )
            )

        if response.get("fix_commands"):
            console.print("\n[bold green]🔧 Suggested Fixes:[/bold green]")

            for i, fix in enumerate(response["fix_commands"], 1):
                console.print(
                    Panel(
                        f"[bold white]{fix.get('command', '')}[/bold white]\n"
                        f"[dim]{fix.get('explanation', '')}[/dim]",
                        title=f"[green]Fix {i}[/green]",
                        border_style="green",
                        padding=(0, 2),
                    )
                )

        if response.get("prevention"):
            console.print(
                Panel(
                    Markdown(response["prevention"]),
                    title="[bold blue]💡 How to prevent this[/bold blue]",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if response.get("references"):
            console.print("\n[bold]📚 References:[/bold]")
            for ref in response["references"]:
                console.print(f"  [cyan]{ref.get('title', '')}[/cyan] -> {ref.get('url', '')}")

    def _apply_fixes(self, fix_commands: list):

        console.print("\n[bold yellow]⚡ Auto-Fix Mode[/bold yellow]")

        SAFE_PREFIXES = (
            "pip install",
            "pip3 install",
            "npm install",
            "yarn add",
            "apt-get install",
        )

        for fix in fix_commands:
            cmd = fix.get("command", "").strip()

            if not cmd:
                continue

            is_safe = cmd.startswith(SAFE_PREFIXES)

            if is_safe:
                console.print(f"[green]▶ Running:[/green] {cmd}")

                try:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode == 0:
                        console.print("[green]✓ Success[/green]")
                    else:
                        console.print(f"[red]✗ Failed:[/red] {result.stderr.strip()}")

                except Exception as e:
                    console.print(f"[red]✗ Execution error:[/red] {str(e)}")

            else:
                console.print(f"[yellow]⚠ Skipped (unsafe):[/yellow] {cmd}")

    def _show_parsed_info(self, parsed: dict):
        console.print("\n[dim]--- Debug Parser Output ---[/dim]")
        import json
        console.print_json(json.dumps(parsed, indent=2))
        console.print("[dim]---------------------------[/dim]\n")
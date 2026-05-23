"""
AI Terminal Debug Assistant - CLI Entry Point
"""

import typer
import sys
import subprocess
import os
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.live import Live

from src.core.debugger import DebugSession
from src.core.config import Config

app = typer.Typer(
    name="debugai",
    help="🤖 AI Terminal Debug Assistant — explains errors and suggests fixes instantly.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def run(
    command: Optional[str] = typer.Argument(None, help="Command to run and debug"),
    error_input: Optional[str] = typer.Option(None, "--error", "-e", help="Paste error text directly"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="AI model to use"),
    provider: str = typer.Option("openai", "--provider", "-p", help="AI provider: openai or ollama"),
    auto_fix: bool = typer.Option(False, "--auto-fix", "-a", help="Automatically apply safe fixes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed debug info"),
):
    """
    Run a command and debug any errors with AI assistance.

    Examples:

        debugai run "python app.py"

        debugai run --error "ModuleNotFoundError: No module named 'dotenv'"

        echo "your error" | debugai run
    """
    config = Config(model=model, provider=provider, verbose=verbose)
    session = DebugSession(config)

    # Banner
    console.print(
        Panel(
            "[bold cyan]🤖 AI Terminal Debug Assistant[/bold cyan]\n"
            "[dim]Powered by LLM + smart error parsing[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )

    error_text = None

    # Priority: --error flag > piped stdin > run command
    if error_input:
        error_text = error_input
    elif not sys.stdin.isatty():
        error_text = sys.stdin.read().strip()
    elif command:
        console.print(f"\n[bold]▶ Running:[/bold] [yellow]{command}[/yellow]\n")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error_text = result.stderr or result.stdout
            console.print(f"[red]✗ Command failed (exit {result.returncode})[/red]\n")
            console.print(Panel(error_text.strip(), title="[red]Error Output[/red]", border_style="red"))
        else:
            console.print("[green]✓ Command succeeded — no errors to debug![/green]")
            console.print(result.stdout)
            return
    else:
        console.print("[yellow]No command or error provided. Use --help for usage.[/yellow]")
        raise typer.Exit(1)

    if error_text:
        session.analyze(error_text, auto_fix=auto_fix)


@app.command()
def explain(
    error: str = typer.Argument(..., help="Error message to explain"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m"),
    provider: str = typer.Option("openai", "--provider", "-p"),
):
    """
    Explain a specific error message.

    Example:

        debugai explain "NameError: name 'x' is not defined"
    """
    config = Config(model=model, provider=provider)
    session = DebugSession(config)
    session.analyze(error)


@app.command()
def history():
    """Show recent debug sessions."""
    from src.core.history import DebugHistory
    h = DebugHistory()
    h.display()


@app.command()
def config_init():
    """Initialize configuration file (~/.debugai/config.yaml)."""
    Config.init_interactive()


def main():
    app()


if __name__ == "__main__":
    main()

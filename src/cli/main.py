import typer
import sys
import subprocess
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from src.core.debugger import DebugSession
from src.core.config import Config

app = typer.Typer(
    name="debugai",
    help="AI Terminal Debug Assistant",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def run(
    command: Optional[str] = typer.Argument(None),
    error_input: Optional[str] = typer.Option(None, "--error", "-e"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    auto_fix: bool = typer.Option(False, "--auto-fix", "-a"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):

    config = Config(
        model=model,
        provider=provider,
        verbose=verbose,
        auto_fix=auto_fix,
    )

    session = DebugSession(config)

    console.print(
        Panel(
            "AI Terminal Debug Assistant",
            border_style="cyan",
        )
    )

    error_text = None

    if error_input:
        error_text = error_input

    elif not sys.stdin.isatty():
        error_text = sys.stdin.read().strip()

    elif command:
        console.print(f"\nRunning: {command}\n")

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            error_text = result.stderr or result.stdout
            console.print(result.stderr or result.stdout)
        else:
            console.print(result.stdout)
            return

    else:
        console.print("No input provided")
        raise typer.Exit(1)

    if error_text:
        session.analyze(error_text, auto_fix=auto_fix)


@app.command()
def explain(
    error: str = typer.Argument(...),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
):

    config = Config(model=model, provider=provider)
    session = DebugSession(config)
    session.analyze(error)


@app.command()
def history():
    from src.core.history import DebugHistory
    DebugHistory().display()


@app.command()
def config_init():
    Config.init_interactive()


def main():
    app()


if __name__ == "__main__":
    main()
"""
Debug session history — stores past sessions in ~/.debugai/history.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

HISTORY_FILE = Path.home() / ".debugai" / "history.json"


class DebugHistory:
    def __init__(self):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.sessions = self._load()

    def _load(self) -> list:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE) as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save(self, error_text: str, parsed: dict, response: dict):
        entry = {
            "id": len(self.sessions) + 1,
            "timestamp": datetime.now().isoformat(),
            "error_type": parsed.get("error_type", "Unknown"),
            "language": parsed.get("language", "Unknown"),
            "error_snippet": error_text[:120],
            "fix_applied": bool(response.get("fix_commands")),
        }
        self.sessions.append(entry)

        # Keep last N sessions
        if len(self.sessions) > 50:
            self.sessions = self.sessions[-50:]

        with open(HISTORY_FILE, "w") as f:
            json.dump(self.sessions, f, indent=2)

    def display(self):
        if not self.sessions:
            console.print("[yellow]No debug history found.[/yellow]")
            return

        table = Table(
            title="🕒 Debug Session History",
            box=box.ROUNDED,
            border_style="cyan",
            show_lines=True,
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Time", style="cyan", width=20)
        table.add_column("Type", style="red")
        table.add_column("Lang", style="green")
        table.add_column("Error Snippet", style="white")
        table.add_column("Fix?", style="bold")

        for s in reversed(self.sessions[-20:]):
            ts = s["timestamp"][:16].replace("T", " ")
            fix_badge = "[green]✓[/green]" if s["fix_applied"] else "[dim]—[/dim]"
            table.add_row(
                str(s["id"]),
                ts,
                s["error_type"],
                s["language"],
                s["error_snippet"][:60] + ("..." if len(s["error_snippet"]) > 60 else ""),
                fix_badge,
            )

        console.print(table)

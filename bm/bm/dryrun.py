"""DryRunContext — collect planned operations without writing anything."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich import box
from rich.console import Console
from rich.table import Table


@dataclass
class DryRunOp:
    verb: str        # "symlink" | "copy" | "remove" | "registry_add" | "registry_remove"
    target: str      # human-readable description of what would change
    source: str = "" # optional source path


@dataclass
class DryRunContext:
    dry_run: bool = False
    ops: list[DryRunOp] = field(default_factory=list)

    def record(self, verb: str, target: str, source: str = "") -> None:
        """Record an operation. No-op when dry_run=False."""
        if self.dry_run:
            self.ops.append(DryRunOp(verb=verb, target=target, source=source))

    @property
    def has_changes(self) -> bool:
        return len(self.ops) > 0

    def render(self, console: Console | None = None) -> None:
        """Print a Rich table of planned operations to stdout."""
        c = console or Console()
        if not self.ops:
            c.print("[dim]No changes would be made.[/]")
            return
        table = Table(title="Dry-run: planned operations", box=box.ROUNDED)
        table.add_column("Action", style="cyan")
        table.add_column("Target")
        table.add_column("Source", style="dim")
        for op in self.ops:
            table.add_row(op.verb, op.target, op.source)
        c.print(table)
        c.print(
            f"[yellow]Dry-run complete — {len(self.ops)} operations would run"
            " (nothing written).[/]"
        )

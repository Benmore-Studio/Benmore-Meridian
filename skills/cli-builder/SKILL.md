---
name: cli-builder
description: Build production-ready CLI tools with Python using Typer, Rich, and modern patterns. Use when creating command-line tools, adding subcommands, building interactive terminal UIs, or scaffolding CLI projects.
triggers:
  - build CLI
  - create CLI tool
  - make command-line tool
  - CLI with Typer
  - Python CLI
  - terminal tool
context: fork
---

# cli-builder

Build production-ready Python CLI tools using Typer + Rich with modern patterns.

## When to Use

- Creating a new CLI tool from scratch
- Adding commands/subcommands to an existing CLI
- Building interactive terminal UIs with Rich
- Setting up CLI project structure with pyproject.toml entry points

## Stack

- **Typer** >= 0.12 — CLI framework (built on Click)
- **Rich** >= 13 — Beautiful terminal output (tables, panels, progress bars)
- **Python** >= 3.11 — For StrEnum, `X | Y` union types, dataclasses

## Project Structure

```
my-tool/
├── my_tool/
│   ├── __init__.py          # __version__ = "1.0.0"
│   ├── cli.py               # Typer app + commands
│   ├── config.py            # Path constants, no side effects at import
│   ├── models.py            # Dataclasses + StrEnums only
│   └── [domain modules]     # Business logic, separate from CLI
├── tests/
│   ├── conftest.py          # Fixtures (tmp dirs, mock data)
│   └── test_*.py            # One test file per module
├── pyproject.toml           # Entry point: my-tool = "my_tool.cli:app"
└── Makefile                 # test, check, fmt, install targets
```

## Patterns

### App Setup

```python
import typer
from rich.console import Console

app = typer.Typer(name="my-tool", help="What it does", add_completion=False)
sub_app = typer.Typer(help="Manage sub-things")
app.add_typer(sub_app, name="sub")

console = Console()
```

### Default Command (Dashboard)

```python
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Show dashboard when no subcommand given."""
    if ctx.invoked_subcommand is not None:
        return
    _render_dashboard()
```

### Commands with Options

```python
@app.command()
def setup(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip prompts"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only"),
) -> None:
    """One-line description shown in --help."""
    ...
```

### Subcommands

```python
@sub_app.command("list")
def sub_list(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List all sub-things."""
    if json_output:
        console.print(json.dumps(data, indent=2))
        return
    table = Table(box=box.ROUNDED)
    ...
```

### Rich Output

```python
from rich.table import Table
from rich.panel import Panel
from rich import box

# Tables
table = Table(title="Results", box=box.ROUNDED)
table.add_column("Name", style="cyan")
table.add_column("Status", justify="center")
table.add_row("item", "✅")
console.print(table)

# Panels
console.print(Panel("content", title="Title", border_style="blue"))

# Section dividers
console.rule("[bold]Section Name[/]")

# Status messages
console.print("[green]✅ Done![/]")
console.print("[red]❌ Failed:[/] reason")
console.print("[yellow]⚠  Warning:[/] details")
console.print("[dim]Skipped: reason[/]")
```

### Dry-Run Support

```python
@dataclass
class DryRunContext:
    dry_run: bool = False
    ops: list = field(default_factory=list)

    def record(self, verb: str, target: str) -> None:
        self.ops.append((verb, target))

    def render(self, console: Console) -> None:
        if not self.ops:
            console.print("[dim]Nothing to do.[/]")
            return
        table = Table(title="Dry-run", box=box.SIMPLE)
        table.add_column("Action")
        table.add_column("Target")
        for verb, target in self.ops:
            table.add_row(verb, target)
        console.print(table)
```

### JSON Output for Agents

Always support `--json` on list/status commands so AI agents can consume output:

```python
if json_output:
    console.print(json.dumps([asdict(e) for e in entries], indent=2))
    return
# else render Rich table
```

### Confirmation Prompts

```python
if not yes:
    typer.confirm(f"Install {len(missing)} tools?", default=True, abort=True)
```

### Cross-Platform Support

```python
import sys

def _is_macos() -> bool:
    return sys.platform == "darwin"

def _is_linux() -> bool:
    return sys.platform.startswith("linux")

def _is_windows() -> bool:
    return sys.platform == "win32"
```

### pyproject.toml Entry Point

```toml
[project.scripts]
my-tool = "my_tool.cli:app"
```

Install with: `pip install -e .` or `uv pip install -e .`

## Anti-Patterns

- Don't put business logic in cli.py — keep it in domain modules
- Don't use `click` directly — Typer wraps it with better ergonomics
- Don't use `argparse` — Typer is strictly better for modern Python
- Don't use interactive menus for commands agents need to call — support `--yes`
- Don't forget `--json` on list commands — agents need machine-readable output
- Don't hardcode paths — use a `config.py` module with `Path` constants

## Testing

```python
from typer.testing import CliRunner
from my_tool.cli import app

runner = CliRunner()

def test_install():
    result = runner.invoke(app, ["install"])
    assert result.exit_code == 0
    assert "Done" in result.output
```

## Makefile

```makefile
.PHONY: test check fmt install

install:
	uv sync --all-extras

test:
	uv run pytest

check:
	uv run ruff check bm/ tests/
	uv run mypy bm/

fmt:
	uv run ruff format bm/ tests/
	uv run ruff check --fix bm/ tests/

check-all: check test
```

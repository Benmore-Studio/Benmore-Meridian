"""Prompt user-state registry: stars, usage counts, last-used timestamps."""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class PromptState:
    """User-level state for a single prompt (not in git — lives in ~/.bm/)."""

    starred: bool = False
    use_count: int = 0
    last_used: str = ""

    def record_use(self) -> None:
        self.use_count += 1
        self.last_used = datetime.now(timezone.utc).isoformat()


class PromptRegistry:
    """Manages ~/.bm/prompts.json for stars and usage tracking."""

    def __init__(self, registry_file: Path) -> None:
        self._file = registry_file
        self._entries: dict[str, PromptState] = {}
        if registry_file.exists():
            self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            # Corrupt registry — start fresh rather than crashing
            return
        for name, d in data.items():
            self._entries[name] = PromptState(
                starred=d.get("starred", False),
                use_count=d.get("use_count", 0),
                last_used=d.get("last_used", ""),
            )

    def save(self) -> None:
        """Persist registry atomically (write to temp, then rename)."""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        data = {name: asdict(entry) for name, entry in self._entries.items()}
        try:
            fd, tmp = tempfile.mkstemp(
                dir=self._file.parent, prefix=".bm_", suffix=".tmp"
            )
            try:
                with open(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                Path(tmp).replace(self._file)
            except Exception:
                Path(tmp).unlink(missing_ok=True)
                raise
        except OSError:
            # Fallback: direct write if atomic fails (e.g. cross-device)
            self._file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, name: str) -> PromptState:
        if name not in self._entries:
            self._entries[name] = PromptState()
        return self._entries[name]

    def star(self, name: str) -> None:
        state = self.get(name)
        state.starred = True
        self.save()

    def unstar(self, name: str) -> None:
        state = self.get(name)
        state.starred = False
        self.save()

    def record_use(self, name: str) -> None:
        state = self.get(name)
        state.record_use()
        self.save()

    def list_starred(self) -> list[str]:
        return [name for name, s in self._entries.items() if s.starred]

    def list_by_popularity(self) -> list[tuple[str, int]]:
        return sorted(
            [(name, s.use_count) for name, s in self._entries.items()],
            key=lambda x: x[1],
            reverse=True,
        )

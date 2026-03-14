"""SkillMatcher — scans a project directory and scores installed skills by relevance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SkillSuggestion:
    """A skill ranked by relevance to the scanned project."""

    name: str
    reason: str    # human-readable explanation, e.g. "django in pyproject.toml"
    status: str    # "installed" or "available"
    score: int     # higher = more relevant


class SkillMatcher:
    """Scans a project directory and scores available skills by relevance."""

    def __init__(self, skills_dir: Path, claude_skills_dir: Path) -> None:
        self._skills_dir = skills_dir
        self._claude_skills_dir = claude_skills_dir
        self._keyword_index: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(
        self,
        path: Path,
        top: int = 8,
        exclude_installed: bool = False,
    ) -> list[SkillSuggestion]:
        """Return up to *top* skills ranked by relevance to the project at *path*."""
        self._build_keyword_index()
        signals, reasons = self._detect_signals(path)
        installed = self._installed_skill_names()

        suggestions: list[SkillSuggestion] = []
        for skill_name, keywords in self._keyword_index.items():
            matches = [kw for kw in keywords if kw in signals]
            if not matches:
                continue
            is_installed = skill_name in installed
            if exclude_installed and is_installed:
                continue
            reason = self._best_reason(matches, reasons)
            suggestions.append(
                SkillSuggestion(
                    name=skill_name,
                    reason=reason,
                    status="installed" if is_installed else "available",
                    score=len(matches),
                )
            )

        suggestions.sort(key=lambda s: s.score, reverse=True)
        return suggestions[:top]

    def stack_summary(self, path: Path) -> str:
        """Return a short human-readable tech-stack string for the project at *path*."""
        signals, _ = self._detect_signals(path)

        parts: list[str] = []

        # Language / framework tier
        if "django" in signals:
            parts.append("Python/Django")
        elif "fastapi" in signals:
            parts.append("Python/FastAPI")
        elif "flask" in signals:
            parts.append("Python/Flask")
        elif any(s in signals for s in ("python", "pyproject")):
            parts.append("Python")

        if "nextjs" in signals or "next.js" in signals:
            parts.append("Next.js")
        elif "react" in signals and "mobile" not in signals:
            parts.append("React")

        if "react-native" in signals or "expo" in signals:
            parts.append("React Native")
            if "expo" in signals:
                parts.append("Expo")

        if "typescript" in signals:
            parts.append("TypeScript")

        # Background / infra tier
        if "celery" in signals:
            parts.append("Celery")
        if "redis" in signals:
            parts.append("Redis")
        if "postgres" in signals or "postgresql" in signals:
            parts.append("PostgreSQL")
        if "docker" in signals:
            parts.append("Docker")
        if "github-actions" in signals or "ci" in signals:
            parts.append("GitHub Actions")

        if not parts:
            return "Unknown stack"

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique.append(p)

        return " · ".join(unique)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_keyword_index(self) -> None:
        """Populate self._keyword_index from each skill's SKILL.md."""
        self._keyword_index = {}
        if not self._skills_dir.is_dir():
            return
        for skill_md in self._skills_dir.rglob("SKILL.md"):
            skill_name = skill_md.parent.name
            triggers = self._parse_triggers(skill_md)
            if triggers:
                self._keyword_index[skill_name] = [t.lower() for t in triggers]

    def _parse_triggers(self, skill_md: Path) -> list[str]:
        """Extract triggers list from SKILL.md frontmatter (no YAML library)."""
        try:
            lines = skill_md.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []

        # Check for frontmatter delimiters
        if not lines or lines[0].strip() != "---":
            return self._fallback_keywords(lines[:30])

        in_fm = False
        in_triggers = False
        triggers: list[str] = []

        for line in lines[1:]:
            if line.strip() == "---":
                if not in_fm:
                    in_fm = True
                    continue
                else:
                    break  # end of frontmatter

            if not in_fm:
                in_fm = True

            if line.startswith("triggers:"):
                in_triggers = True
                # handles inline: triggers: [a, b]
                inline = line[len("triggers:"):].strip()
                if inline.startswith("["):
                    items = re.findall(r"['\"]?([A-Za-z0-9_./ -]+)['\"]?", inline)
                    triggers.extend(i.strip() for i in items if i.strip())
                    in_triggers = False
                continue

            if in_triggers:
                if line.startswith("  ") or line.startswith("\t"):
                    # list item: "  - keyword"
                    m = re.match(r"[\s\t]+-\s+(.*)", line)
                    if m:
                        triggers.append(m.group(1).strip().strip("\"'"))
                else:
                    in_triggers = False  # left the triggers block

        return triggers if triggers else self._fallback_keywords(lines[:30])

    def _fallback_keywords(self, lines: list[str]) -> list[str]:
        """Extract bare keywords from the first 30 lines when no frontmatter found."""
        text = " ".join(lines).lower()
        candidates = re.findall(r"\b([a-z][a-z0-9._-]{2,})\b", text)
        # Keep only plausible tech terms (short common words filtered)
        stop = {"the", "and", "for", "with", "use", "this", "that", "are", "you",
                "can", "will", "from", "when", "your", "also", "all", "not",
                "how", "any", "new", "its", "has", "was", "but", "our"}
        return [c for c in dict.fromkeys(candidates) if c not in stop][:20]

    def _detect_signals(self, path: Path) -> tuple[set[str], dict[str, str]]:
        """Return (signal_set, signal→reason_string) for the project at *path*."""
        signals: set[str] = set()
        reasons: dict[str, str] = {}

        def add(signal: str, reason: str) -> None:
            signals.add(signal)
            reasons.setdefault(signal, reason)

        # pyproject.toml / requirements / setup.py
        for pfile in ["pyproject.toml", "setup.py", "setup.cfg"]:
            fpath = path / pfile
            if fpath.exists():
                add("python", f"python project ({pfile})")
                add("pyproject", pfile)
                self._extract_python_packages(fpath, signals, reasons)

        for req in path.glob("requirements*.txt"):
            self._extract_python_packages(req, signals, reasons)

        # package.json
        pkg_json = path / "package.json"
        if pkg_json.exists():
            self._extract_npm_packages(pkg_json, signals, reasons)

        # Docker
        if (path / "Dockerfile").exists():
            add("docker", "Dockerfile")
        dcompose = path / "docker-compose.yml"
        if dcompose.exists():
            add("docker", "docker-compose.yml")
            try:
                text = dcompose.read_text(encoding="utf-8", errors="replace").lower()
                if "redis" in text:
                    add("redis", "redis service in docker-compose.yml")
                if "postgres" in text:
                    add("postgres", "postgres service in docker-compose.yml")
            except OSError:
                pass

        # GitHub Actions
        if (path / ".github" / "workflows").is_dir():
            add("github-actions", ".github/workflows/")
            add("ci", ".github/workflows/")

        # manage.py → Django
        if (path / "manage.py").exists():
            add("django", "manage.py")

        # Celery
        for celery_file in list(path.glob("celery*.py")) + list(path.rglob("tasks.py")):
            if celery_file.exists():
                add("celery", str(celery_file.relative_to(path)))
                break

        # Mobile / frontend top-level dirs
        if (path / "mobile").is_dir():
            add("react-native", "mobile/ directory")
            add("mobile", "mobile/ directory")
            add("expo", "mobile/ directory")

        if (path / "frontend").is_dir():
            add("frontend", "frontend/ directory")
            add("react", "frontend/ directory")
            add("nextjs", "frontend/ directory")

        # Makefile
        if (path / "Makefile").exists():
            add("makefile", "Makefile")

        return signals, reasons

    def _extract_python_packages(
        self, fpath: Path, signals: set[str], reasons: dict[str, str]
    ) -> None:
        """Parse Python dependency files and add package names as signals."""
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            return

        # Strip version specifiers: "django>=4.0" → "django"
        pkg_re = re.compile(r"([a-z][a-z0-9_-]+)")
        filename = fpath.name

        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            m = pkg_re.match(line)
            if m:
                pkg = m.group(1).rstrip("-_")
                # Normalise common aliases
                pkg = pkg.replace("_", "-")
                if pkg and len(pkg) > 1:
                    signals.add(pkg)
                    reasons.setdefault(pkg, f"{pkg} in {filename}")

    def _extract_npm_packages(
        self, pkg_json: Path, signals: set[str], reasons: dict[str, str]
    ) -> None:
        """Pull dependency names from package.json without a JSON library is fine,
        but we use stdlib json here (it's in stdlib)."""
        import json  # stdlib

        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            return

        all_deps: dict[str, str] = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))

        name_map = {
            "next": "nextjs",
            "react-native": "react-native",
            "expo": "expo",
            "react": "react",
            "typescript": "typescript",
            "celery": "celery",
            "django": "django",
            "fastapi": "fastapi",
        }

        for dep in all_deps:
            dep_lower = dep.lower().lstrip("@").split("/")[-1]
            canonical = name_map.get(dep_lower, dep_lower)
            signals.add(canonical)
            reasons.setdefault(canonical, f"{dep} in package.json")

    def _installed_skill_names(self) -> set[str]:
        """Return set of skill names present in claude_skills_dir."""
        if not self._claude_skills_dir.is_dir():
            return set()
        return {p.name for p in self._claude_skills_dir.iterdir()}

    def _best_reason(self, matches: list[str], reasons: dict[str, str]) -> str:
        """Pick the most informative reason string from matched signals."""
        # Prefer the match with the most descriptive reason
        for match in matches:
            r = reasons.get(match, "")
            if r:
                return r
        return ", ".join(matches[:2])

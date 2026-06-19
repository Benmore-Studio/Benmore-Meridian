"""SkillMatcher — scans a project directory and scores installed skills by relevance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SkillSuggestion:
    """A skill ranked by relevance to the scanned project."""

    name: str
    reason: str  # human-readable explanation, e.g. "django in pyproject.toml"
    status: str  # "installed" or "available"
    score: int  # higher = more relevant
    category: str = "Other"


CATEGORY_ALIASES: dict[str, list[str]] = {
    "Security & Compliance": [
        "audit",
        "compliance",
        "gdpr",
        "hipaa",
        "hippa",
        "soc2",
        "soc-2",
        "security",
        "tenant",
        "phi",
        "pii",
        "auth",
        "2fa",
        "mfa",
        "totp",
        "otp",
    ],
    "Backend": [
        "api",
        "backend",
        "celery",
        "django",
        "fastapi",
        "flask",
        "kafka",
        "service",
        "socket",
        "realtime",
    ],
    "Frontend": [
        "frontend",
        "react",
        "nextjs",
        "next.js",
        "ui",
        "web",
        "playwright",
        "threejs",
    ],
    "Mobile": ["expo", "mobile", "push", "react-native"],
    "Deployment": ["deploy", "deployment", "digitalocean", "doctl", "heroku", "sentry", "vercel"],
    "Documents": ["doc", "docx", "pdf", "presentation", "release", "xlsx"],
    "SEO": ["seo", "search", "programmatic"],
    "Payments": ["stripe", "payment", "billing"],
    "Finance": ["financial", "finance", "accounting", "invoice"],
    "Benmore": ["benmore", "project", "ticket", "scope", "client"],
}


INTENT_SKILL_SETS: dict[str, list[str]] = {
    "seo": ["ai-seo", "seo-audit", "programmatic-seo", "site-capture"],
    "search": ["ai-seo", "seo-audit", "programmatic-seo", "site-capture"],
    "security": [
        "dependency-security-audit",
        "security-compliance-audit",
        "multi-tenant-scan",
        "multi-tenant-guard",
    ],
    "hipaa": [
        "hipaa-compliance-guard",
        "healthcare-audit-logger",
        "audit-trail",
        "security-compliance-audit",
    ],
    "soc2": ["security-compliance-audit", "audit-trail", "dependency-security-audit"],
    "gdpr": ["gdpr-compliance", "audit-trail", "security-compliance-audit"],
    "auth": ["universal-auth", "role-based-authentication", "django-react-2fa", "otp-verification"],
    "payments": ["stripe-best-practices", "stripe-integration", "upgrade-stripe"],
    "stripe": ["stripe-best-practices", "stripe-integration", "upgrade-stripe"],
    "frontend": ["frontend-productionize", "web-design-guidelines", "minimalist-ui-design"],
    "docs": ["docx", "pdf", "presentation-maker", "release-notes"],
}


SKILL_CATEGORY_OVERRIDES: dict[str, str] = {
    "audit-trail": "Security & Compliance",
    "dependency-security-audit": "Security & Compliance",
    "django-react-2fa": "Security & Compliance",
    "gdpr-compliance": "Security & Compliance",
    "healthcare-audit-logger": "Security & Compliance",
    "hipaa-compliance-guard": "Security & Compliance",
    "multi-tenant-guard": "Security & Compliance",
    "multi-tenant-scan": "Security & Compliance",
    "otp-verification": "Security & Compliance",
    "role-based-authentication": "Security & Compliance",
    "security-compliance-audit": "Security & Compliance",
    "service-invariant-guard": "Security & Compliance",
    "universal-auth": "Security & Compliance",
    "django-auth-react-native": "Backend",
    "django-celery-expert": "Backend",
    "django-production": "Backend",
    "fastapi-templates": "Backend",
    "productionize-app": "Backend",
    "realtime-socket-react-query": "Backend",
    "frontend-productionize": "Frontend",
    "minimalist-ui-design": "Frontend",
    "playwright-doc-generator": "Frontend",
    "site-capture": "Frontend",
    "threejs-architect": "Frontend",
    "web-design-guidelines": "Frontend",
    "expo-push-notifications": "Mobile",
    "push-notifications-firebase": "Mobile",
    "apple-release": "Mobile",
    "doctl-cli": "Deployment",
    "heroku-cli": "Deployment",
    "sentry-cli": "Deployment",
    "vercel-cli": "Deployment",
    "docx": "Documents",
    "pdf": "Documents",
    "presentation-maker": "Documents",
    "presentation_maker": "Documents",
    "release-notes": "Documents",
    "xlsx": "Documents",
    "ai-seo": "SEO",
    "programmatic-seo": "SEO",
    "seo-audit": "SEO",
    "stripe-best-practices": "Payments",
    "stripe-integration": "Payments",
    "stripe-projects": "Payments",
    "stripe_processing": "Payments",
    "upgrade-stripe": "Payments",
    "benmore-api": "Benmore",
    "better-scope-gen": "Benmore",
    "client-value-maximizer": "Benmore",
    "feature-alignment": "Benmore",
    "gh_issue": "Benmore",
    "github-issue-gen": "Benmore",
    "project-primer": "Benmore",
    "tickets": "Benmore",
    "using-bm": "Benmore",
    "financial-audit": "Finance",
}


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
                    category=self.category_for_skill(skill_name),
                )
            )

        suggestions.sort(key=lambda s: (-s.score, s.category, s.name))
        return suggestions[:top]

    def scan_intent(
        self,
        intent: str,
        top: int = 8,
        exclude_installed: bool = False,
    ) -> list[SkillSuggestion]:
        """Return skills ranked by a natural-language task intent."""
        self._build_keyword_index()
        signals, reasons = self._detect_intent_signals(intent)
        installed = self._installed_skill_names()
        preferred = self._preferred_skills_for_signals(signals)

        suggestions_by_name: dict[str, SkillSuggestion] = {}
        for rank, skill_name in enumerate(preferred):
            if (
                skill_name not in self._keyword_index
                and not (self._skills_dir / skill_name / "SKILL.md").exists()
            ):
                continue
            is_installed = skill_name in installed
            if exclude_installed and is_installed:
                continue
            signal = self._preferred_reason_signal(skill_name, signals)
            suggestions_by_name[skill_name] = SkillSuggestion(
                name=skill_name,
                reason=reasons.get(signal, f"{signal} in task intent"),
                status="installed" if is_installed else "available",
                score=100 - rank,
                category=self.category_for_skill(skill_name),
            )

        for skill_name, keywords in self._keyword_index.items():
            matches = [kw for kw in keywords if kw in signals]
            if not matches:
                continue
            is_installed = skill_name in installed
            if exclude_installed and is_installed:
                continue
            existing = suggestions_by_name.get(skill_name)
            score = len(matches)
            if existing is not None:
                existing.score += score
                continue
            suggestions_by_name[skill_name] = SkillSuggestion(
                name=skill_name,
                reason=self._best_reason(matches, reasons),
                status="installed" if is_installed else "available",
                score=score,
                category=self.category_for_skill(skill_name),
            )

        suggestions = list(suggestions_by_name.values())
        suggestions.sort(key=lambda s: (-s.score, s.category, s.name))
        return suggestions[:top]

    def catalog_by_category(self) -> dict[str, list[str]]:
        """Return all repo skills grouped into stable, human-friendly categories."""
        grouped: dict[str, list[str]] = {}
        if not self._skills_dir.is_dir():
            return grouped
        for skill_md in self._skills_dir.rglob("SKILL.md"):
            if skill_md.parent == self._skills_dir:
                continue
            name = skill_md.parent.name
            grouped.setdefault(self.category_for_skill(name), []).append(name)
        return {category: sorted(names) for category, names in sorted(grouped.items())}

    def category_for_skill(self, skill_name: str) -> str:
        """Return the display category for a skill name."""
        if skill_name in SKILL_CATEGORY_OVERRIDES:
            return SKILL_CATEGORY_OVERRIDES[skill_name]
        normalized = skill_name.replace("_", "-").lower()
        for category, aliases in CATEGORY_ALIASES.items():
            if any(alias in normalized for alias in aliases):
                return category
        return "Other"

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
        """Populate self._keyword_index from each skill's SKILL.md (cached after first call)."""
        if self._keyword_index:
            return
        if not self._skills_dir.is_dir():
            return
        for skill_md in self._skills_dir.rglob("SKILL.md"):
            skill_name = skill_md.parent.name
            triggers = self._parse_triggers(skill_md)
            triggers.extend(self._name_aliases(skill_name))
            if triggers:
                self._keyword_index[skill_name] = list(dict.fromkeys(t.lower() for t in triggers))

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
                inline = line[len("triggers:") :].strip()
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

    def _name_aliases(self, skill_name: str) -> list[str]:
        """Keywords inferred from the skill slug and category."""
        aliases = skill_name.replace("_", "-").split("-")
        category = self.category_for_skill(skill_name)
        aliases.extend(CATEGORY_ALIASES.get(category, []))
        aliases.append(skill_name.replace("_", "-"))
        return aliases

    def _fallback_keywords(self, lines: list[str]) -> list[str]:
        """Extract bare keywords from the first 30 lines when no frontmatter found."""
        text = " ".join(lines).lower()
        candidates = re.findall(r"\b([a-z][a-z0-9._-]{2,})\b", text)
        # Keep only plausible tech terms (short common words filtered)
        stop = {
            "the",
            "and",
            "for",
            "with",
            "use",
            "this",
            "that",
            "are",
            "you",
            "can",
            "will",
            "from",
            "when",
            "your",
            "also",
            "all",
            "not",
            "how",
            "any",
            "new",
            "its",
            "has",
            "was",
            "but",
            "our",
        }
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
            if (path / "frontend" / "next.config.js").exists() or (
                path / "frontend" / "next.config.ts"
            ).exists():
                add("nextjs", "frontend/next.config.js")

        # Makefile
        if (path / "Makefile").exists():
            add("makefile", "Makefile")

        self._extract_repo_text_signals(path, add)

        return signals, reasons

    def _detect_intent_signals(self, intent: str) -> tuple[set[str], dict[str, str]]:
        """Return signal keywords from a free-form task description."""
        normalized = intent.lower().replace("_", "-")
        tokens = set(re.findall(r"[a-z][a-z0-9+.-]*", normalized))
        signals: set[str] = set(tokens)
        reasons: dict[str, str] = {token: f"{token} in task intent" for token in tokens}

        phrase_signals = {
            "seo": ["seo", "search engine", "search visibility", "organic traffic"],
            "search": ["search engine", "search visibility", "organic traffic"],
            "programmatic": ["programmatic seo", "landing pages"],
            "security": ["security", "secure", "vulnerability", "secrets"],
            "hipaa": ["hipaa", "phi", "healthcare"],
            "soc2": ["soc 2", "soc2"],
            "gdpr": ["gdpr", "privacy"],
            "auth": ["auth", "authentication", "authorization", "login"],
            "2fa": ["2fa", "mfa", "totp", "otp"],
            "stripe": ["stripe", "payments", "billing"],
            "payments": ["payments", "billing"],
            "frontend": ["frontend", "ui", "react", "next.js"],
            "docs": ["docs", "documentation", "write a guide", "release notes"],
        }
        for signal, phrases in phrase_signals.items():
            if signal in signals or any(phrase in normalized for phrase in phrases):
                signals.add(signal)
                reasons.setdefault(signal, f"{signal} in task intent")

        if "improve" in signals and "seo" in signals:
            signals.update({"search", "programmatic", "site", "content"})
            for signal in ("search", "programmatic", "site", "content"):
                reasons.setdefault(signal, "improve seo in task intent")

        return signals, reasons

    def _preferred_skills_for_signals(self, signals: set[str]) -> list[str]:
        preferred: list[str] = []
        for signal, skill_names in INTENT_SKILL_SETS.items():
            if signal in signals:
                preferred.extend(skill_names)
        return list(dict.fromkeys(preferred))

    def _preferred_reason_signal(self, skill_name: str, signals: set[str]) -> str:
        for signal, skill_names in INTENT_SKILL_SETS.items():
            if signal in signals and skill_name in skill_names:
                return signal
        return next(iter(signals), "intent")

    def _extract_repo_text_signals(self, path: Path, add: Any) -> None:
        """Scan small project metadata files for compliance, auth, and delivery signals."""
        files = [
            "AGENTS.md",
            "CLAUDE.md",
            "README.md",
            "SECURITY.md",
            "SOC2.md",
            "HIPAA.md",
            ".env.example",
            "docker-compose.yml",
            "docker-compose.yaml",
            "package.json",
            "pyproject.toml",
        ]
        text_parts: list[str] = []
        for name in files:
            fpath = path / name
            if fpath.exists() and fpath.is_file():
                try:
                    text_parts.append(fpath.read_text(encoding="utf-8", errors="replace").lower())
                except OSError:
                    continue

        for candidate in [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-prod.txt",
            "next.config.js",
            "next.config.ts",
            "sentry.properties",
        ]:
            fpath = path / candidate
            if fpath.exists() and fpath.is_file():
                try:
                    text_parts.append(fpath.read_text(encoding="utf-8", errors="replace").lower())
                except OSError:
                    continue

        text = "\n".join(text_parts)
        if not text:
            return

        keyword_signals = {
            "hipaa": ["hipaa", "phi", "protected health"],
            "soc2": ["soc 2", "soc2", "trust service"],
            "gdpr": ["gdpr", "data subject", "right to erasure"],
            "security": ["security", "csp", "csrf", "xss", "vulnerability", "secrets"],
            "audit": ["audit log", "audit trail", "immutable log"],
            "multi-tenant": ["multi-tenant", "multitenant", "tenant isolation", "tenant_id"],
            "auth": ["authentication", "authorization", "jwt", "oauth", "rbac"],
            "2fa": ["2fa", "mfa", "totp", "one-time password", "otp"],
            "stripe": ["stripe", "paymentintent", "checkout session"],
            "sentry": ["sentry", "dsn"],
            "vercel": ["vercel"],
            "heroku": ["heroku"],
            "digitalocean": ["digitalocean", "doctl"],
            "seo": ["seo", "sitemap", "robots.txt", "search console"],
            "playwright": ["playwright", "e2e"],
            "pdf": ["pdf"],
            "docx": ["docx"],
            "xlsx": ["xlsx", "spreadsheet"],
        }
        for signal, needles in keyword_signals.items():
            for needle in needles:
                if needle in text:
                    add(signal, f"{needle} in project metadata")
                    break

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

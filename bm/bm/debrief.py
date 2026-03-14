from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import subprocess


CURSOR_FILE = Path.home() / ".bm" / "debrief_cursor"

REUSABLE_NOUNS = {
    "handler", "pipeline", "service", "middleware", "validator",
    "processor", "builder", "parser", "formatter", "integration",
    "connector",
}

CANDIDATE_PREFIXES = {"feat", "add", "refactor", "introduce"}


@dataclass
class SkillCandidate:
    name: str       # suggested slug (e.g. "stripe-webhook-handler")
    rationale: str  # why this was flagged (1-2 sentences)
    score: int      # confidence score (higher = more confident)
    command: str    # "bm skill write <name>"


def load_cursor() -> str | None:
    """Read last debrief timestamp from ~/.bm/debrief_cursor."""
    if CURSOR_FILE.exists():
        text = CURSOR_FILE.read_text().strip()
        return text if text else None
    return None


def save_cursor(timestamp: str) -> None:
    """Write current ISO timestamp to ~/.bm/debrief_cursor."""
    CURSOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    CURSOR_FILE.write_text(timestamp)


def _run_git(args: list[str]) -> str | None:
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def _to_slug(phrase: str) -> str:
    """Normalize a noun phrase to a hyphenated slug."""
    slug = phrase.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def _existing_skill_names() -> set[str]:
    """Return set of slugs already installed in ~/.claude/skills/."""
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return set()
    return {p.name for p in skills_dir.iterdir() if p.is_dir() or p.is_symlink()}


def run_debrief(
    repo_root: Path,
    limit: int = 15,
    since: str | None = None,
) -> list[SkillCandidate]:
    """Read recent git history and identify candidate skills worth codifying."""
    # Use cursor if no explicit since provided
    if since is None:
        since = load_cursor()

    # Build log command
    log_args = ["git", "-C", str(repo_root), "log", "--oneline"]
    if since:
        log_args.append(f"--since={since}")
    else:
        log_args.append(f"-{limit}")

    log_output = _run_git(log_args)
    if not log_output:
        save_cursor(datetime.now().isoformat())
        return []

    commits = [line.strip() for line in log_output.strip().splitlines() if line.strip()]
    if len(commits) < 3:
        save_cursor(datetime.now().isoformat())
        return []

    # Determine diff range
    oldest_hash = commits[-1].split()[0]
    newest_hash = commits[0].split()[0]
    diff_range = f"{oldest_hash}~1..{newest_hash}"

    # Get changed files and added files
    stat_output = _run_git(["git", "-C", str(repo_root), "diff", diff_range, "--stat"]) or ""
    names_output = _run_git(["git", "-C", str(repo_root), "diff", diff_range, "--name-only"]) or ""
    added_output = _run_git(
        ["git", "-C", str(repo_root), "diff", diff_range, "--name-only", "--diff-filter=A"]
    ) or ""

    added_files: set[str] = set(added_output.strip().splitlines())

    # Count CLAUDE.md line additions
    claude_md_bonus = 0
    claude_diff = _run_git(
        ["git", "-C", str(repo_root), "diff", diff_range, "--", "CLAUDE.md"]
    ) or ""
    added_paragraphs = len(re.findall(r"^\+[^+].*\S", claude_diff, re.MULTILINE))
    claude_md_bonus = min(added_paragraphs // 5, 3)  # cap at +3, 1 per ~5 added lines

    existing_skills = _existing_skill_names()

    # Parse commit subjects for candidate slugs
    slug_counts: dict[str, int] = {}
    slug_subjects: dict[str, list[str]] = {}

    for commit_line in commits:
        parts = commit_line.split(" ", 1)
        if len(parts) < 2:
            continue
        subject = parts[1].strip()

        colon_idx = subject.find(":")
        if colon_idx == -1:
            continue

        prefix = subject[:colon_idx].strip().lower()
        # Strip scope like "feat(auth)" → "feat"
        prefix = re.sub(r"\(.*?\)", "", prefix).strip()

        if prefix not in CANDIDATE_PREFIXES:
            continue

        noun_phrase = subject[colon_idx + 1:].strip()
        # Remove leading "a", "an", "the"
        noun_phrase = re.sub(r"^(a|an|the)\s+", "", noun_phrase, flags=re.IGNORECASE)
        slug = _to_slug(noun_phrase)

        if not slug or len(slug) < 3:
            continue

        slug_counts[slug] = slug_counts.get(slug, 0) + 1
        slug_subjects.setdefault(slug, []).append(subject)

    # Score candidates
    candidates: dict[str, SkillCandidate] = {}

    for slug, count in slug_counts.items():
        score = 0
        reasons: list[str] = []

        if count >= 2:
            score += 2
            reasons.append(f"appears in {count} commit subjects")

        # Check for reusable nouns in the slug itself
        slug_words = set(slug.split("-"))
        matched_nouns = slug_words & REUSABLE_NOUNS
        if matched_nouns:
            score += 1
            reasons.append(f"contains reusable pattern noun ({', '.join(matched_nouns)})")

        # Check if any added files relate to this slug
        slug_stem = slug.replace("-", "")
        for f in added_files:
            file_stem = Path(f).stem.lower().replace("_", "").replace("-", "")
            if slug_stem in file_stem or file_stem in slug_stem:
                score += 1
                reasons.append("introduced new files")
                break

        if claude_md_bonus > 0:
            score += claude_md_bonus
            reasons.append(f"CLAUDE.md gained ~{added_paragraphs} new lines")

        if slug not in existing_skills:
            score += 1
            reasons.append("not yet an installed skill")

        if score >= 3:
            rationale = "; ".join(reasons).capitalize() + "."
            candidates[slug] = SkillCandidate(
                name=slug,
                rationale=rationale,
                score=score,
                command=f"bm skill write {slug}",
            )

    save_cursor(datetime.now().isoformat())

    sorted_candidates = sorted(candidates.values(), key=lambda c: c.score, reverse=True)
    return sorted_candidates[:5]

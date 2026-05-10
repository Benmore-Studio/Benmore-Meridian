"""
intent_matcher.py — Cosine-similarity intent router.

Pre-computes centroids for each intent (mean of embedded example phrases),
then matches a user message against them to skip the LLM on common requests.

Cost: 1 OpenAI embedding call per request (~30ms, ~$0.00002 with
`text-embedding-3-small`).

Saves ~80% of LLM round trips in production for chatbots with ≥ 5 high-
frequency intents.

See references/intent-routing.md for tuning guidance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

import numpy as np
import openai

logger = logging.getLogger(__name__)


# ─── Confidence bands ──────────────────────────────────────────────────────

class Confidence(str, Enum):
    HIGH      = "high"        # >= THRESHOLD_HIGH
    MEDIUM    = "medium"      # >= THRESHOLD_MEDIUM
    AMBIGUOUS = "ambiguous"   # top-2 delta < AMBIGUITY_DELTA
    LOW       = "low"         # >= THRESHOLD_LOW
    NO_MATCH  = "no_match"    # < THRESHOLD_LOW


THRESHOLD_HIGH    = 0.85
THRESHOLD_MEDIUM  = 0.70
THRESHOLD_LOW     = 0.50
AMBIGUITY_DELTA   = 0.05


# ─── Intent definitions ────────────────────────────────────────────────────

@dataclass
class IntentDefinition:
    """One intent with example phrases for embedding."""

    name: str                       # must match a tool name in ALL_HANDLERS
    description: str                # used in clarification prompts and metrics
    example_phrases: list[str]      # 5-10 paraphrases — drives the centroid
    requires_pro: bool = False
    read_only: bool = False
    is_destructive: bool = False    # gate behind a confirmation word


@dataclass
class IntentMatch:
    """Result of matching a user message."""

    intent: str
    confidence: Confidence
    score: float
    description: str
    requires_pro: bool = False
    read_only: bool = False
    is_destructive: bool = False
    runner_up: str | None = None
    runner_up_score: float = 0.0
    all_scores: dict[str, float] = field(default_factory=dict)


# Replace these with your own intents. Keep ~7 phrases per intent for
# robustness without paying boot-time embedding overhead.
INTENT_DEFINITIONS: list[IntentDefinition] = [
    IntentDefinition(
        name="create_customer",
        description="Create a new customer in the system",
        example_phrases=[
            "add a new client",
            "register a customer",
            "new contact",
            "create customer named",
            "add a customer",
            "save new client details",
            "I need to add someone to my customers",
        ],
    ),
    IntentDefinition(
        name="search_customers",
        description="Search customers by name, email, or company",
        example_phrases=[
            "find customer",
            "look up a client",
            "search for",
            "do we have a customer named",
            "show customers matching",
            "which clients have",
        ],
        read_only=True,
    ),
    IntentDefinition(
        name="navigate",
        description="Navigate to a page in the app",
        example_phrases=[
            "go to dashboard",
            "show me invoices",
            "open settings",
            "take me to customers",
            "navigate to",
            "jump to",
        ],
        read_only=True,
    ),
    IntentDefinition(
        name="general_chat",
        description="Open-ended conversation that doesn't fit a specific tool",
        example_phrases=[
            "explain how this works",
            "what does this number mean",
            "tell me about",
            "why is",
            "how do I",
        ],
        read_only=True,
    ),
    # ... add more intents (one per high-frequency tool)
]


# ─── The matcher ───────────────────────────────────────────────────────────

class IntentMatcher:
    """Embeds intents on first use, then matches per-request."""

    EMBEDDING_MODEL = "text-embedding-3-small"

    # Class-level cache so all instances share the same centroids.
    _intent_vectors: dict[str, np.ndarray] | None = None
    _intent_meta:    dict[str, IntentDefinition] | None = None

    def __init__(self, client: openai.OpenAI | None = None) -> None:
        self.client = client or openai.OpenAI()

    # ---------- bootstrap ----------------------------------------------------

    def _ensure_vectors(self) -> None:
        """Compute and cache intent centroids on first use."""
        if IntentMatcher._intent_vectors is not None:
            return

        logger.info("Computing intent centroids for %d intents", len(INTENT_DEFINITIONS))
        vectors: dict[str, np.ndarray] = {}
        meta:    dict[str, IntentDefinition] = {}

        # Batch all phrases for one API call (much cheaper than per-intent).
        all_phrases: list[str] = []
        bounds: list[tuple[int, int]] = []  # (start, end) per intent
        for intent_def in INTENT_DEFINITIONS:
            start = len(all_phrases)
            all_phrases.extend(intent_def.example_phrases)
            bounds.append((start, len(all_phrases)))

        embeddings = self._embed_batch(all_phrases)
        if not embeddings:
            logger.error("Failed to embed intent phrases; matcher disabled.")
            IntentMatcher._intent_vectors = {}
            IntentMatcher._intent_meta = {}
            return

        embeddings_arr = np.array(embeddings)
        for intent_def, (start, end) in zip(INTENT_DEFINITIONS, bounds):
            phrase_vecs = embeddings_arr[start:end]
            centroid = phrase_vecs.mean(axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm   # L2-normalize for cosine = dot
            vectors[intent_def.name] = centroid
            meta[intent_def.name] = intent_def

        IntentMatcher._intent_vectors = vectors
        IntentMatcher._intent_meta = meta
        logger.info("Cached %d intent centroids", len(vectors))

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            resp = self.client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=texts,
            )
            return [d.embedding for d in resp.data]
        except openai.OpenAIError:
            logger.exception("Embedding batch failed")
            return []

    def _embed_single(self, text: str) -> np.ndarray | None:
        try:
            resp = self.client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=[text],
            )
            vec = np.array(resp.data[0].embedding)
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        except openai.OpenAIError:
            logger.exception("Embedding single failed")
            return None

    # ---------- the actual match --------------------------------------------

    def match(self, message: str) -> IntentMatch:
        """Score `message` against all intents; return the best match."""
        self._ensure_vectors()

        user_vec = self._embed_single(message)
        if user_vec is None:
            return IntentMatch(
                intent="general_chat",
                confidence=Confidence.NO_MATCH,
                score=0.0,
                description="Failed to embed message",
            )

        intent_vectors = IntentMatcher._intent_vectors or {}
        intent_meta    = IntentMatcher._intent_meta or {}

        # Cosine similarity = dot product on L2-normalized vectors.
        scores: dict[str, float] = {
            name: float(np.dot(user_vec, vec))
            for name, vec in intent_vectors.items()
        }
        if not scores:
            return IntentMatch(
                intent="general_chat",
                confidence=Confidence.NO_MATCH,
                score=0.0,
                description="No intents available",
            )

        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_name, best_score = sorted_intents[0]
        runner_name, runner_score = (
            sorted_intents[1] if len(sorted_intents) > 1 else (None, 0.0)
        )
        best_meta = intent_meta[best_name]

        # Banding logic — see references/intent-routing.md for the full table.
        if best_score >= THRESHOLD_HIGH:
            confidence = (
                Confidence.AMBIGUOUS
                if runner_name and (best_score - runner_score) < AMBIGUITY_DELTA
                else Confidence.HIGH
            )
        elif best_score >= THRESHOLD_MEDIUM:
            confidence = (
                Confidence.AMBIGUOUS
                if runner_name and (best_score - runner_score) < AMBIGUITY_DELTA
                else Confidence.MEDIUM
            )
        elif best_score >= THRESHOLD_LOW:
            confidence = Confidence.LOW
        else:
            confidence = Confidence.NO_MATCH

        return IntentMatch(
            intent=best_name,
            confidence=confidence,
            score=best_score,
            description=best_meta.description,
            requires_pro=best_meta.requires_pro,
            read_only=best_meta.read_only,
            is_destructive=best_meta.is_destructive,
            runner_up=runner_name,
            runner_up_score=runner_score,
            all_scores=scores,
        )


@lru_cache(maxsize=1)
def get_intent_matcher() -> IntentMatcher:
    """Process-level singleton."""
    return IntentMatcher()

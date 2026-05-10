# pyright: reportMissingImports=false, reportArgumentType=false
# Note: This is a SCAFFOLD. `chat_tools` and Django imports won't resolve
# until you copy this file into a real project and adapt the imports.
"""
chat_service.py — Multi-turn OpenAI tool-calling loop.

Copy this into your codebase and adapt:
  - Replace the import for `dispatch_tool` with your project's path.
  - Replace the import for `ALL_TOOLS` (the schema list).
  - Replace the SYSTEM_PROMPT with your domain's prompt (use the template
    in assets/system-prompt-template.md as a starting point).
  - Replace the `get_openai_client()` factory if you have your own.

Why this file exists:
  - The conditional `tools` kwarg on the final turn is THE fix that makes
    multi-turn tool calling work cleanly. Explicit `tools=None` is rejected
    by the API; you must omit the kwarg to force a text summary on turn N.
  - Centralized error handling distinguishes domain errors (return error
    envelope) from programming bugs (let them propagate to your error
    tracker).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache

import openai

# Adjust these imports for your project layout.
from chat_tools import ALL_TOOLS, dispatch_tool

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
You are an AI assistant for [YOUR APP].

When the user asks you to do something, CALL THE APPROPRIATE TOOL. Do NOT
say "I'll do that for you" or "Let me do that" — those phrases are wasted
tokens. Just call the tool. Only respond in plain text after a tool has
returned, or if the user is asking a question that doesn't require a tool.

Available tools cover [DOMAINS]. When in doubt, call a search/list tool to
ground yourself before calling a write tool.

When a tool returns {"error": "requires_pro", ...}, write a brief upsell
message linking to /settings/subscription. Do not retry the tool.

When a tool returns {"error": "<other>"}, decide whether to retry with
different args, ask the user for clarification, or apologize and stop.
"""


@lru_cache(maxsize=1)
def get_openai_client() -> openai.OpenAI:
    """Return a process-level singleton OpenAI client.

    The lru_cache reuses the underlying httpx connection pool across
    requests. If you have your own factory (with secrets manager, etc.),
    use it instead.
    """
    return openai.OpenAI()  # picks up OPENAI_API_KEY from env


class ChatService:
    """Multi-turn tool-calling chat session.

    One instance per request. Not thread-safe — don't share across requests.
    """

    MAX_TURNS = 5
    MODEL = "gpt-4o"
    MAX_TOKENS = 500  # per turn; tune for your domain

    TOOLS = ALL_TOOLS

    def __init__(self, user) -> None:
        # Adapt this guard for your auth model. The user object is passed
        # to every dispatched handler, so handlers can scope queries by
        # user.organization (or your tenant key).
        self.user = user
        self.client = get_openai_client()

    # ---------------------------------------------------------------- public

    def process_message(
        self, message: str, conversation_history: list | None = None
    ) -> dict:
        """Run the multi-turn loop. Returns {"response": str, "actions": list}.

        `conversation_history` is a list of {"role", "content"} dicts. We trim
        to the last 20 to stay within context limits.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_history:
            messages.extend(conversation_history[-20:])
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                tools=self.TOOLS,
                tool_choice="auto",
                max_tokens=self.MAX_TOKENS,
            )
        except openai.OpenAIError:
            logger.exception("OpenAI API error in chat service (initial)")
            return {
                "response": "Sorry, I'm having trouble connecting to my AI service. "
                            "Try again in a moment.",
                "actions": [],
            }

        actions_taken: list[dict] = []

        # MAX_TURNS bounds runaway loops. In practice 2-3 turns covers anything.
        for turn in range(self.MAX_TURNS):
            choice = response.choices[0]

            # No tool calls → done. Return the model's text response.
            if not choice.message.tool_calls:
                return {
                    "response": choice.message.content,
                    "actions": actions_taken,
                }

            # Append the assistant message containing tool_calls BEFORE results.
            # The API requires this ordering.
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                result = self._execute_tool(tool_call.function.name, args)
                actions_taken.append(
                    {
                        "tool": tool_call.function.name,
                        "args": args,
                        "result": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

            # ### CONDITIONAL TOOLS KWARG (THE IMPORTANT BIT) ###
            # On the final turn, omit `tools` entirely to force a text summary.
            # Explicit `tools=None` / `tool_choice=None` is REJECTED by the API.
            kwargs = {
                "model": self.MODEL,
                "messages": messages,
                "max_tokens": self.MAX_TOKENS,
            }
            if turn < self.MAX_TURNS - 1:
                kwargs["tools"] = self.TOOLS
                kwargs["tool_choice"] = "auto"

            try:
                response = self.client.chat.completions.create(**kwargs)
            except openai.OpenAIError:
                logger.exception("OpenAI API error in chat follow-up (turn %d)", turn)
                return {
                    "response": "I completed part of the action but couldn't finish "
                                "the summary. Check the page for results.",
                    "actions": actions_taken,
                }

        # Hit MAX_TURNS without an exit; return whatever the model said last.
        choice = response.choices[0]
        return {
            "response": choice.message.content
            or "I tried several steps but didn't reach a clean stopping point.",
            "actions": actions_taken,
        }

    # ---------------------------------------------------------------- private

    def _execute_tool(self, name: str, args: dict) -> dict:
        """Dispatch + structured error handling.

        Programming bugs (AttributeError, KeyError, TypeError) are NOT
        caught — they propagate to your error tracker. Domain exceptions
        get user-facing envelopes.
        """
        # Adapt these imports for your framework.
        from django.core.exceptions import (
            PermissionDenied,
            ValidationError as DjangoValidationError,
        )
        from django.db import IntegrityError

        try:
            return dispatch_tool(self.user, name, args)
        except IntegrityError:
            logger.exception("IntegrityError in tool %s", name)
            return {"error": "That value conflicts with existing data. "
                             "Try different values or check for duplicates."}
        except PermissionDenied:
            return {"error": "You don't have permission to do that."}
        except (DjangoValidationError, ValueError) as exc:
            return {"error": str(exc)}
        except openai.OpenAIError:
            # Tool itself called OpenAI (e.g. AI description generator).
            logger.exception("OpenAI error inside tool %s", name)
            return {"error": "AI service is temporarily unavailable. Try again."}

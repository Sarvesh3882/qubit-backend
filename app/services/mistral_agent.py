"""
Mistral AI provider layer for QUBIT's AI tutor.

Two call paths:

  1. Agents API  (preferred when MISTRAL_AGENT_ID is set)
     ─────────────────────────────────────────────────────
     POST https://api.mistral.ai/v1/agents/completions
     Uses a pre-configured Mistral Agent from Mistral Studio.
     The agent carries its own system instructions and tool config.
     QUBIT injects dynamic context (lesson, code, sim) as the first
     user message prefix before the actual user question.

  2. Chat Completions  (fallback when only MISTRAL_API_KEY is set)
     ───────────────────────────────────────────────────────────────
     POST https://api.mistral.ai/v1/chat/completions
     Uses `settings.MISTRAL_MODEL` (default: mistral-small-latest).
     Full QUBIT system prompt is sent as the system role.

Both paths are async-safe (blocking SDK calls run in a thread pool).
All errors are raised as MistralAgentError to be caught by the endpoint.

Environment variables (all read from settings — never hardcoded):
  MISTRAL_API_KEY     — required for either path
  MISTRAL_AGENT_ID    — selects the Agents path
  MISTRAL_MODEL       — selects the model for Chat Completions path
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class MistralAgentError(Exception):
    """Raised when the Mistral call fails in a way the endpoint should handle."""


def _get_client():
    """Return a configured Mistral SDK client. Raises if no API key."""
    if not settings.MISTRAL_API_KEY:
        raise MistralAgentError(
            "MISTRAL_API_KEY is not configured. "
            "Add it to .env to enable the AI assistant."
        )
    from mistralai.client import Mistral  # lazy import
    return Mistral(api_key=settings.MISTRAL_API_KEY)


def _build_context_prefix(context_dict: dict[str, Any]) -> str:
    """
    Build a short plaintext block that is prepended to the user message
    when using the Agents API.  The agent's own system instructions handle
    persona and pedagogy — this only injects the *dynamic* QUBIT state.
    """
    lines: list[str] = ["[QUBIT context]"]

    if context_dict.get("path_title"):
        lines.append(f"Learning path: {context_dict['path_title']}")
    if context_dict.get("module_title"):
        lines.append(f"Module: {context_dict['module_title']}")
    if context_dict.get("lesson_title"):
        lines.append(f"Lesson: {context_dict['lesson_title']}")
    if context_dict.get("current_concept"):
        lines.append(f"Concept: {context_dict['current_concept']}")
    completed = context_dict.get("completed_lessons", [])
    if completed:
        lines.append(f"Lessons completed so far: {len(completed)}")
    if (context_dict.get("current_code") or "").strip():
        code = context_dict["current_code"][:1200]
        lines.append(f"Current code:\n```python\n{code}\n```")
    sim = context_dict.get("simulation_result")
    if isinstance(sim, dict) and sim.get("success"):
        probs = sim.get("probabilities", {})
        top = sorted(probs.items(), key=lambda x: -x[1])[:4]
        prob_str = ", ".join(f"|{s}⟩: {p:.0%}" for s, p in top)
        lines.append(f"Latest simulation: {prob_str}")

    if len(lines) == 1:
        return ""  # no context worth sending
    return "\n".join(lines) + "\n\n"


def _call_agents_api(
    messages: list[dict[str, str]],
    agent_id: str,
) -> str:
    """Synchronous call to Mistral Agents API (run in thread pool)."""
    client = _get_client()
    response = client.agents.complete(
        agent_id=agent_id,
        messages=messages,
        max_tokens=700,
        timeout_ms=30_000,
    )
    return response.choices[0].message.content


def _call_chat_api(
    messages: list[dict[str, str]],
    model: str,
) -> str:
    """Synchronous call to Mistral Chat Completions API (run in thread pool)."""
    client = _get_client()
    # chat.complete is sync; complete_async needs an event loop
    response = client.chat.complete(
        model=model,
        messages=messages,
        max_tokens=700,
        temperature=0.4,
        timeout_ms=30_000,
    )
    return response.choices[0].message.content


async def call_mistral(
    *,
    user_message: str,
    system_prompt: str,
    history: list[dict[str, str]],
    context_dict: dict[str, Any],
) -> str:
    """
    Async entry point called by the FastAPI endpoint.

    Selects Agents API or Chat Completions based on settings, builds the
    message list, and runs the blocking SDK call in a thread pool executor.

    Returns the reply string.
    Raises MistralAgentError on any failure.
    """
    agent_id: Optional[str] = (settings.MISTRAL_AGENT_ID or "").strip() or None
    model: str = (settings.MISTRAL_MODEL or "mistral-small-latest").strip()

    try:
        if agent_id:
            # ── Agents API path ──────────────────────────────────────────────
            # The agent carries its own system instructions.
            # We inject dynamic QUBIT context as a prefix on the user message.
            context_prefix = _build_context_prefix(context_dict)
            augmented_user_msg = context_prefix + user_message

            messages: list[dict[str, str]] = []
            # History: strip system messages; agents API takes only user/assistant
            for h in history[-8:]:
                if h.get("role") in ("user", "assistant"):
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": augmented_user_msg})

            logger.info(
                "Calling Mistral Agents API  agent=%s  turns=%d",
                agent_id[:20], len(messages),
            )
            reply = await asyncio.get_event_loop().run_in_executor(
                None, _call_agents_api, messages, agent_id
            )

        else:
            # ── Chat Completions path ────────────────────────────────────────
            messages = [{"role": "system", "content": system_prompt}]
            for h in history[-8:]:
                if h.get("role") in ("user", "assistant"):
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": user_message})

            logger.info(
                "Calling Mistral Chat Completions  model=%s  turns=%d",
                model, len(messages),
            )
            reply = await asyncio.get_event_loop().run_in_executor(
                None, _call_chat_api, messages, model
            )

        return reply

    except MistralAgentError:
        raise
    except Exception as exc:
        logger.warning("Mistral call failed: %s", exc)
        raise MistralAgentError(f"Mistral API error: {exc}") from exc

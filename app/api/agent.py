"""
Context-aware AI Agent API for QUBIT.

The agent receives a structured context payload (current lesson, module, path,
code, circuit, simulation results, learner history) plus a user message, and
returns a pedagogically grounded response.

Architecture
------------
Provider priority:
  1. Mistral Agents API  — when MISTRAL_API_KEY + MISTRAL_AGENT_ID are set.
     The pre-configured Mistral Agent carries its own system instructions.
     QUBIT injects dynamic learner context as a prefix on the user message.

  2. Mistral Chat Completions  — when only MISTRAL_API_KEY is set.
     Uses MISTRAL_MODEL (default: mistral-small-latest) with the full
     QUBIT system prompt injected as the system role.

  3. Local rule/template fallback  — when no Mistral key is configured.
     Keyword-matching engine with curated quantum knowledge. Always works,
     even in offline or dev environments.

RAG-lite: relevant lesson theory excerpts are injected into the system prompt
(for Chat Completions path) or the context prefix (for Agents path) so the
model can refer to actual QUBIT content.
"""

from __future__ import annotations

import logging
import re
import textwrap
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.services.curriculum import get_lesson, get_all_paths
from app.services.mistral_agent import call_mistral, MistralAgentError

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)

# ── Request / response models ─────────────────────────────────────────────────

class AgentContext(BaseModel):
    path_id: Optional[str] = None
    path_title: Optional[str] = None
    module_id: Optional[str] = None
    module_title: Optional[str] = None
    lesson_id: Optional[str] = None
    lesson_title: Optional[str] = None
    current_code: Optional[str] = None
    simulation_result: Optional[dict[str, Any]] = None
    completed_lessons: list[str] = []
    current_concept: Optional[str] = None


class AgentMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AgentRequest(BaseModel):
    message: str
    context: AgentContext = AgentContext()
    history: list[AgentMessage] = []


class AgentResponse(BaseModel):
    reply: str
    suggestions: list[str] = []
    context_used: list[str] = []


# ── System prompt builder ─────────────────────────────────────────────────────

def _build_system_prompt(context: AgentContext) -> str:
    parts = [
        "You are QUBIT's AI learning assistant — a friendly, expert quantum computing tutor.",
        "Your goal is to help learners *understand* quantum concepts, not just give them answers.",
        "Always explain the reasoning behind your answers.",
        "Use LaTeX math notation ($...$) for equations.",
        "Keep answers focused and appropriately detailed for the learner's current position.",
        "",
        "QUBIT platform context:",
    ]

    if context.path_title:
        parts.append(f"- Learning Path: {context.path_title}")
    if context.module_title:
        parts.append(f"- Current Module: {context.module_title}")
    if context.lesson_title:
        parts.append(f"- Current Lesson: {context.lesson_title}")
    if context.current_concept:
        parts.append(f"- Concept being studied: {context.current_concept}")
    if context.completed_lessons:
        parts.append(f"- Learner has completed {len(context.completed_lessons)} lessons so far.")

    if context.current_code and context.current_code.strip():
        parts += [
            "",
            "The learner's current code:",
            "```python",
            context.current_code[:1200],
            "```",
            "If asked about the code, refer to it specifically.",
        ]

    if context.simulation_result:
        sr = context.simulation_result
        if sr.get("success"):
            probs = sr.get("probabilities", {})
            top = sorted(probs.items(), key=lambda x: -x[1])[:4]
            prob_str = ", ".join(f"|{s}⟩: {p:.1%}" for s, p in top)
            parts += [
                "",
                f"Latest simulation results: {prob_str}",
                "If relevant, help the learner interpret these probabilities.",
            ]

    # Inject relevant lesson theory as RAG context
    if context.path_id and context.module_id and context.lesson_id:
        lesson = get_lesson(context.path_id, context.module_id, context.lesson_id)
        if lesson:
            theory_blocks = [b for b in lesson.get("content", []) if b["type"] == "theory"]
            if theory_blocks:
                parts += ["", "Relevant lesson theory (use this to ground your answers):"]
                for b in theory_blocks[:2]:
                    body = b.get("body", "")[:600]
                    parts.append(f"[{b['title']}]: {body}")

    parts += [
        "",
        "Respond in a clear, encouraging tone.",
        "If the learner is stuck on code, guide them with hints rather than giving the full solution.",
        "If asked about a concept not yet covered, briefly introduce it and suggest the relevant lesson.",
    ]
    return "\n".join(parts)


# ── Local fallback knowledge base ─────────────────────────────────────────────

KNOWLEDGE_BASE: dict[str, str] = {
    "qubit": (
        "A **qubit** is the fundamental unit of quantum information. Unlike a classical bit (0 or 1), "
        "a qubit can be in a *superposition* of both states:\n\n"
        "$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$\n\n"
        "where $|\\alpha|^2 + |\\beta|^2 = 1$. The values $|\\alpha|^2$ and $|\\beta|^2$ are the "
        "probabilities of measuring 0 or 1 respectively."
    ),
    "superposition": (
        "**Superposition** means a qubit can exist in a combination of $|0\\rangle$ and $|1\\rangle$ "
        "simultaneously. The Hadamard gate $H$ creates an equal superposition:\n\n"
        "$$H|0\\rangle = \\frac{|0\\rangle + |1\\rangle}{\\sqrt{2}}$$\n\n"
        "Measuring this state gives 0 or 1 with 50% probability each."
    ),
    "hadamard": (
        "The **Hadamard gate** $H$ is one of the most important single-qubit gates:\n\n"
        "$$H = \\frac{1}{\\sqrt{2}}\\begin{pmatrix}1 & 1 \\\\ 1 & -1\\end{pmatrix}$$\n\n"
        "It maps $|0\\rangle \\to |+\\rangle$ and $|1\\rangle \\to |-\\rangle$, "
        "creating equal superpositions. Applying $H$ twice returns to the original state."
    ),
    "entanglement": (
        "**Entanglement** is a uniquely quantum correlation between qubits. "
        "The Bell state $|\\Phi^+\\rangle = (|00\\rangle + |11\\rangle)/\\sqrt{2}$ is maximally entangled: "
        "measuring one qubit instantly determines the other.\n\n"
        "Create it with: H on qubit 0, then CNOT(0→1). "
        "Entanglement is a key resource in quantum teleportation, cryptography, and algorithms."
    ),
    "cnot": (
        "The **CNOT** (Controlled-NOT) gate flips the *target* qubit if and only if the *control* qubit is $|1\\rangle$:\n\n"
        "$$|00\\rangle \\to |00\\rangle, \\quad |01\\rangle \\to |01\\rangle$$\n"
        "$$|10\\rangle \\to |11\\rangle, \\quad |11\\rangle \\to |10\\rangle$$\n\n"
        "Together with single-qubit gates, CNOT forms a **universal gate set**."
    ),
    "measurement": (
        "**Measuring** a qubit collapses its superposition to a definite state. "
        "For $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$:\n\n"
        "- Outcome $|0\\rangle$ with probability $|\\alpha|^2$\n"
        "- Outcome $|1\\rangle$ with probability $|\\beta|^2$\n\n"
        "Measurement is irreversible — the state collapses and cannot be 'un-measured'."
    ),
    "normalization": (
        "A quantum state must be **normalized**: $|\\alpha|^2 + |\\beta|^2 = 1$. "
        "This ensures probabilities sum to 1.\n\n"
        "To normalize a vector $(\\alpha, \\beta)$, divide by the norm:\n\n"
        "$$|\\psi'\\rangle = \\frac{\\alpha|0\\rangle + \\beta|1\\rangle}{\\sqrt{|\\alpha|^2 + |\\beta|^2}}$$"
    ),
    "bloch sphere": (
        "The **Bloch sphere** is a geometric representation of a single qubit state:\n\n"
        "$$|\\psi\\rangle = \\cos(\\theta/2)|0\\rangle + e^{i\\phi}\\sin(\\theta/2)|1\\rangle$$\n\n"
        "Every pure single-qubit state maps to a point on the unit sphere. "
        "$|0\\rangle$ is the north pole, $|1\\rangle$ the south pole, "
        "and equal superpositions live on the equator."
    ),
    "unitary": (
        "A **unitary matrix** $U$ satisfies $UU^\\dagger = I$. All quantum gates are unitary, which guarantees:\n\n"
        "1. **Reversibility** — quantum evolution can always be undone ($U^{-1} = U^\\dagger$)\n"
        "2. **Norm preservation** — total probability stays 1\n\n"
        "The Pauli gates $X$, $Y$, $Z$ and Hadamard $H$ are all unitary and self-inverse."
    ),
    "grover": (
        "**Grover's algorithm** searches an unsorted database of $N$ items in $O(\\sqrt{N})$ queries, "
        "compared to $O(N)$ classically — a quadratic speedup.\n\n"
        "It works by *amplitude amplification*: repeatedly applying an oracle (marks the target) "
        "and a diffusion operator (reflects around the mean) to boost the target state's probability."
    ),
    "deutsch-jozsa": (
        "The **Deutsch-Jozsa algorithm** determines in a *single* quantum query whether a function "
        "$f: \\{0,1\\}^n \\to \\{0,1\\}$ is constant or balanced.\n\n"
        "Classically this requires up to $2^{n-1}+1$ queries in the worst case. "
        "This was the first demonstration of exponential quantum speedup."
    ),
    "qft": (
        "The **Quantum Fourier Transform** (QFT) is the quantum analog of the DFT, computed in $O(\\log^2 n)$ "
        "operations vs $O(n \\log n)$ classically.\n\n"
        "It's a core subroutine in Shor's algorithm and Quantum Phase Estimation (QPE)."
    ),
    "bell state": (
        "The **Bell states** are the four maximally entangled 2-qubit states:\n\n"
        "$$|\\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$$\n"
        "$$|\\Phi^-\\rangle = \\frac{|00\\rangle - |11\\rangle}{\\sqrt{2}}$$\n\n"
        "Prepare $|\\Phi^+\\rangle$ with: H(q0), CNOT(q0, q1). "
        "Bell states are used in teleportation, superdense coding, and quantum key distribution."
    ),
    "pauli": (
        "The **Pauli matrices** are the fundamental single-qubit operators:\n\n"
        "$$X = \\begin{pmatrix}0&1\\\\1&0\\end{pmatrix}, \\quad "
        "Y = \\begin{pmatrix}0&-i\\\\i&0\\end{pmatrix}, \\quad "
        "Z = \\begin{pmatrix}1&0\\\\0&-1\\end{pmatrix}$$\n\n"
        "$X$ flips the qubit (quantum NOT), $Z$ flips the phase, $Y$ does both."
    ),
}


def _local_response(message: str, context: AgentContext) -> AgentResponse:
    """Rule-based fallback when no LLM is configured."""
    msg_lower = message.lower()

    # Check knowledge base keywords
    for keyword, explanation in KNOWLEDGE_BASE.items():
        if keyword in msg_lower:
            suggestions = _get_suggestions(context)
            return AgentResponse(
                reply=explanation,
                suggestions=suggestions,
                context_used=["local_knowledge_base"],
            )

    # Code-specific help
    if any(w in msg_lower for w in ["error", "bug", "wrong", "fix", "debug", "why isn't", "doesn't work"]):
        reply = (
            "Let me help you debug this. A few things to check:\n\n"
            "1. **Array indexing** — Python uses 0-based indexing. Qubit 0 is the first qubit.\n"
            "2. **Complex numbers** — use `complex` or `np.array([...], dtype=complex)` for quantum states.\n"
            "3. **Normalization** — ensure $|\\alpha|^2 + |\\beta|^2 = 1$ for your state vector.\n"
            "4. **Matrix shapes** — a 2-qubit gate is a 4×4 matrix; a single-qubit gate is 2×2.\n\n"
        )
        if context.current_code:
            reply += "Looking at your code, try running it step by step and print intermediate values to isolate where it diverges from your expectation."
        return AgentResponse(reply=reply, suggestions=_get_suggestions(context), context_used=["debug_template"])

    # Hint request
    if any(w in msg_lower for w in ["hint", "stuck", "help", "how do i", "how to"]):
        reply = (
            "Here are some guiding questions to get you unstuck:\n\n"
            "- What is the expected mathematical output of this step?\n"
            "- What does the function/gate need to *do* to the quantum state?\n"
            "- Can you write out the calculation on paper first, then translate it to code?\n\n"
            "Remember: in quantum computing, every operation on a state vector is a **matrix multiplication**. "
            "If you know the matrix and the input state, you can compute the output by hand."
        )
        if context.lesson_title:
            reply += f"\n\nYou're working on *{context.lesson_title}* — check the theory panel on the right for the relevant mathematical definitions."
        return AgentResponse(reply=reply, suggestions=_get_suggestions(context), context_used=["hint_template"])

    # Simulation result interpretation
    if context.simulation_result and context.simulation_result.get("success"):
        probs = context.simulation_result.get("probabilities", {})
        if any(w in msg_lower for w in ["result", "output", "probability", "probabilities", "what does"]):
            top = sorted(probs.items(), key=lambda x: -x[1])[:3]
            lines = [f"- $|{s}\\rangle$: **{p:.1%}**" for s, p in top]
            reply = (
                "Here's how to interpret your simulation results:\n\n"
                + "\n".join(lines)
                + "\n\nEach bar in the histogram shows the probability of measuring that basis state. "
                "A single tall bar means the circuit produces a deterministic output. "
                "Equal bars indicate a superposition that collapses randomly on each measurement."
            )
            return AgentResponse(reply=reply, suggestions=_get_suggestions(context), context_used=["simulation_result"])

    # Concept explanation
    if any(w in msg_lower for w in ["explain", "what is", "what are", "describe", "tell me about"]):
        reply = (
            "Great question! Here's what I can tell you:\n\n"
            "Quantum computing leverages three key quantum mechanical phenomena:\n\n"
            "1. **Superposition** — qubits can be in combinations of $|0\\rangle$ and $|1\\rangle$\n"
            "2. **Entanglement** — qubits can be correlated in ways impossible classically\n"
            "3. **Interference** — quantum amplitudes can add or cancel to highlight correct answers\n\n"
        )
        if context.lesson_title:
            reply += f"In your current lesson *{context.lesson_title}*, try connecting the concept to the hands-on codercise to make it concrete."
        else:
            reply += "Try the Codebook to explore these concepts step by step with interactive exercises."
        return AgentResponse(reply=reply, suggestions=_get_suggestions(context), context_used=["concept_template"])

    # Default
    reply = (
        "I'm here to help with your quantum learning journey! You can ask me:\n\n"
        "- **Concept explanations** — \"What is superposition?\" / \"Explain the Bloch sphere\"\n"
        "- **Code help** — \"Why is my normalize_state function wrong?\"\n"
        "- **Result interpretation** — \"What do these probabilities mean?\"\n"
        "- **Next steps** — \"What should I learn after Bell states?\"\n"
        "- **Algorithm questions** — \"How does Grover's algorithm work?\"\n\n"
        "What would you like to explore?"
    )
    if context.lesson_title:
        reply = f"You're working on *{context.lesson_title}*. {reply}"
    return AgentResponse(reply=reply, suggestions=_get_suggestions(context), context_used=[])


def _get_suggestions(context: AgentContext) -> list[str]:
    """Generate contextual follow-up suggestions."""
    base = [
        "Explain this concept mathematically",
        "Show me a code example",
        "How does this connect to quantum algorithms?",
    ]
    if context.current_code:
        base.insert(0, "Help me debug my code")
    if context.simulation_result and context.simulation_result.get("success"):
        base.insert(0, "Interpret my simulation results")
    if context.lesson_title:
        base.append(f"What comes after {context.lesson_title}?")
    return base[:4]


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=AgentResponse)
async def chat(request: AgentRequest):
    """
    Route: POST /api/agent/chat

    Priority:
      1. Mistral Agents API  (MISTRAL_API_KEY + MISTRAL_AGENT_ID set)
      2. Mistral Chat Completions  (only MISTRAL_API_KEY set)
      3. Local keyword fallback  (no key — always works)
    """
    if settings.MISTRAL_API_KEY and settings.MISTRAL_API_KEY.strip():
        try:
            system_prompt = _build_system_prompt(request.context)
            context_dict = request.context.model_dump()

            # RAG: inject lesson theory into context dict
            if request.context.path_id and request.context.module_id and request.context.lesson_id:
                lesson = get_lesson(
                    request.context.path_id,
                    request.context.module_id,
                    request.context.lesson_id,
                )
                if lesson:
                    theory = [b for b in lesson.get("content", []) if b["type"] == "theory"]
                    if theory:
                        context_dict["_rag_lesson_theory"] = "\n".join(
                            f"[{b['title']}]: {b.get('body', '')[:500]}"
                            for b in theory[:2]
                        )

            history = [{"role": m.role, "content": m.content} for m in request.history]

            reply = await call_mistral(
                user_message=request.message,
                system_prompt=system_prompt,
                history=history,
                context_dict=context_dict,
            )

            provider = (
                "mistral_agents_api"
                if (settings.MISTRAL_AGENT_ID and settings.MISTRAL_AGENT_ID.strip())
                else "mistral_chat_completions"
            )
            return AgentResponse(
                reply=reply,
                suggestions=_get_suggestions(request.context),
                context_used=[provider, "rag_lesson_content"],
            )

        except MistralAgentError as exc:
            logger.warning("Mistral unavailable, falling back to local: %s", exc)
        except Exception as exc:
            logger.warning("Unexpected error in Mistral path: %s", exc)

    return _local_response(request.message, request.context)


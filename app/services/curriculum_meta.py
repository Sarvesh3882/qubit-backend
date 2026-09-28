"""
CURRICULUM_META — single source of truth for structural facts about the curriculum.

This file drives:
  - Certification eligibility checks (certification.py)
  - Adaptive mastery derivation (adaptive.py)
  - Frontend lesson-count totals (served via /curriculum/meta)

Rules:
  - All lesson IDs, codercise IDs, quiz IDs, and module totals MUST be kept
    in sync with curriculum.py.
  - certification.py and adaptive.py import from here — never hardcode these
    numbers in two places.
  - Quiz IDs follow the pattern: {module_id}-quiz (one quiz per module).
  - Required counts for certification are set conservatively:
      required_lessons   = all lessons that exist
      required_codercises = all codercises that exist
      required_quiz_pass  = pass at least this many module quizzes (score ≥ 70%)
"""

from __future__ import annotations
from typing import Any

# ── Per-module structural facts ────────────────────────────────────────────────

MODULE_META: dict[str, dict[str, Any]] = {
    "iqc": {
        "path_id":     "fqc",
        "title":       "Introduction to Quantum Computing",
        "order":       1,
        "prereq_module_ids": [],          # first module — no prerequisites
        "lesson_ids":  ["iqc-1", "iqc-2", "iqc-3"],
        "codercise_ids": ["iqc-1-c1", "iqc-1-c2", "iqc-1-c3", "iqc-2-c1", "iqc-3-c1"],
        "quiz_id":     "iqc-quiz",
        "concept_codercises": {
            "superposition":  ["iqc-1-c1", "iqc-1-c2", "iqc-1-c3"],
            "normalization":  ["iqc-1-c1"],
            "measurement":    ["iqc-1-c3"],
            "gates":          ["iqc-2-c1"],
        },
    },
    "sq": {
        "path_id":     "fqc",
        "title":       "Single-Qubit Gates",
        "order":       2,
        "prereq_module_ids": ["iqc"],
        "lesson_ids":  ["sq-1", "sq-2"],
        "codercise_ids": ["sq-1-c1", "sq-2-c1"],
        "quiz_id":     "sq-quiz",
        "concept_codercises": {
            "bloch": ["sq-1-c1"],
            "gates": ["sq-2-c1"],
        },
    },
    "mq": {
        "path_id":     "fqc",
        "title":       "Multi-Qubit Systems",
        "order":       3,
        "prereq_module_ids": ["sq"],
        "lesson_ids":  ["mq-1", "mq-2"],
        "codercise_ids": ["mq-1-c1", "mq-2-c1"],
        "quiz_id":     "mq-quiz",
        "concept_codercises": {
            "entanglement": ["mq-1-c1", "mq-2-c1"],
        },
    },
    "qalgo-dj": {
        "path_id":     "fqa",
        "title":       "Deutsch-Jozsa Algorithm",
        "order":       1,
        "prereq_module_ids": ["mq"],      # requires all of fqc first
        "lesson_ids":  ["dj-1"],
        "codercise_ids": ["dj-1-c1"],
        "quiz_id":     "dj-quiz",
        "concept_codercises": {
            "algorithms": ["dj-1-c1"],
            "gates":      ["dj-1-c1"],
        },
    },
    "qalgo-grover": {
        "path_id":     "fqa",
        "title":       "Grover's Search Algorithm",
        "order":       2,
        "prereq_module_ids": ["qalgo-dj"],
        "lesson_ids":  ["grover-1"],
        "codercise_ids": ["grover-1-c1"],
        "quiz_id":     "grover-quiz",
        "concept_codercises": {
            "algorithms": ["grover-1-c1"],
        },
    },
}

# ── Derived convenience lookups ────────────────────────────────────────────────

MODULE_ORDER: list[str] = ["iqc", "sq", "mq", "qalgo-dj", "qalgo-grover"]

MODULE_LESSON_TOTALS: dict[str, int] = {
    mid: len(m["lesson_ids"]) for mid, m in MODULE_META.items()
}

MODULE_CODERCISE_IDS: dict[str, list[str]] = {
    mid: m["codercise_ids"] for mid, m in MODULE_META.items()
}

MODULE_QUIZ_IDS: dict[str, str] = {
    mid: m["quiz_id"] for mid, m in MODULE_META.items()
}

MODULE_PATH: dict[str, str] = {
    mid: m["path_id"] for mid, m in MODULE_META.items()
}

MODULE_CONCEPTS: dict[str, list[str]] = {
    mid: list(m["concept_codercises"].keys()) for mid, m in MODULE_META.items()
}

# All codercise IDs → concept they primarily test
CODERCISE_CONCEPT: dict[str, str] = {
    "iqc-1-c1": "superposition",
    "iqc-1-c2": "superposition",
    "iqc-1-c3": "measurement",
    "iqc-2-c1": "gates",
    "iqc-3-c1": "normalization",
    "sq-1-c1":  "bloch",
    "sq-2-c1":  "gates",
    "mq-1-c1":  "entanglement",
    "mq-2-c1":  "entanglement",
    "dj-1-c1":  "algorithms",
    "grover-1-c1": "algorithms",
}

# ── Per-path facts ─────────────────────────────────────────────────────────────

PATH_META: dict[str, dict[str, Any]] = {
    "fqc": {
        "title":   "Foundations of Quantum Computing",
        "modules": ["iqc", "sq", "mq"],
    },
    "fqa": {
        "title":   "Foundations of Quantum Algorithms",
        "modules": ["qalgo-dj", "qalgo-grover"],
    },
}

def _all_ids(path_id: str, key: str) -> list[str]:
    result = []
    for mid in PATH_META[path_id]["modules"]:
        result.extend(MODULE_META[mid].get(key, []))
    return result

PATH_ALL_LESSON_IDS: dict[str, list[str]] = {
    pid: _all_ids(pid, "lesson_ids") for pid in PATH_META
}

PATH_ALL_CODERCISE_IDS: dict[str, list[str]] = {
    pid: _all_ids(pid, "codercise_ids") for pid in PATH_META
}

PATH_ALL_QUIZ_IDS: dict[str, list[str]] = {
    pid: [MODULE_META[mid]["quiz_id"] for mid in PATH_META[pid]["modules"]]
    for pid in PATH_META
}

# ── Certification requirements ─────────────────────────────────────────────────
#
# required_lessons:    learner must complete ALL lessons in the path
# required_codercises: learner must PASS ALL codercises (at least one passing run)
# required_quizzes:    learner must pass at least N module quizzes at ≥ passing_quiz_score
# passing_quiz_score:  minimum score (0–100) to count a quiz as passed
#
# These are the ONLY place these numbers live. certification.py reads from here.

CERT_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "fqc": {
        "path_title":          "Foundations of Quantum Computing",
        "required_lessons":    len(PATH_ALL_LESSON_IDS["fqc"]),       # 7
        "required_codercises": len(PATH_ALL_CODERCISE_IDS["fqc"]),    # 9
        "required_quizzes":    2,   # must pass at least 2 of the 3 module quizzes
        "passing_quiz_score":  70,  # ≥ 70% to count a quiz as passed
        "total_quizzes":       len(PATH_ALL_QUIZ_IDS["fqc"]),         # 3
        "lesson_ids":          PATH_ALL_LESSON_IDS["fqc"],
        "codercise_ids":       PATH_ALL_CODERCISE_IDS["fqc"],
        "quiz_ids":            PATH_ALL_QUIZ_IDS["fqc"],
    },
    "fqa": {
        "path_title":          "Foundations of Quantum Algorithms",
        "required_lessons":    len(PATH_ALL_LESSON_IDS["fqa"]),       # 2
        "required_codercises": len(PATH_ALL_CODERCISE_IDS["fqa"]),    # 2
        "required_quizzes":    1,   # must pass at least 1 of the 2 module quizzes
        "passing_quiz_score":  70,
        "total_quizzes":       len(PATH_ALL_QUIZ_IDS["fqa"]),         # 2
        "lesson_ids":          PATH_ALL_LESSON_IDS["fqa"],
        "codercise_ids":       PATH_ALL_CODERCISE_IDS["fqa"],
        "quiz_ids":            PATH_ALL_QUIZ_IDS["fqa"],
    },
}

# ── Quiz question banks ────────────────────────────────────────────────────────
# Each quiz has multiple-choice questions, each with:
#   id, question, options (list), correct_index (0-based), explanation, concept
#
# These live here so they can be served by the API and scored on the backend.
# We do NOT trust client-reported scores.

QUIZ_QUESTIONS: dict[str, list[dict[str, Any]]] = {

    # ── IQC module quiz ────────────────────────────────────────────────────────
    "iqc-quiz": [
        {
            "id": "iqc-quiz-q1",
            "concept": "superposition",
            "question": "A qubit is in state $|\\psi\\rangle = \\frac{3}{5}|0\\rangle + \\frac{4}{5}|1\\rangle$. What is the probability of measuring $|1\\rangle$?",
            "options": ["9/25", "16/25", "3/5", "4/5"],
            "correct_index": 1,
            "explanation": "$P(|1\\rangle) = |\\beta|^2 = (4/5)^2 = 16/25 = 0.64$.",
        },
        {
            "id": "iqc-quiz-q2",
            "concept": "normalization",
            "question": "Which state is correctly normalized?",
            "options": [
                "$|0\\rangle + |1\\rangle$",
                "$\\frac{1}{\\sqrt{2}}|0\\rangle + \\frac{1}{\\sqrt{2}}|1\\rangle$",
                "$\\frac{3}{4}|0\\rangle + \\frac{1}{4}|1\\rangle$",
                "$2|0\\rangle - |1\\rangle$",
            ],
            "correct_index": 1,
            "explanation": "$|1/\\sqrt{2}|^2 + |1/\\sqrt{2}|^2 = 1/2 + 1/2 = 1$ ✓.",
        },
        {
            "id": "iqc-quiz-q3",
            "concept": "measurement",
            "question": "After measuring a qubit in state $\\alpha|0\\rangle + \\beta|1\\rangle$ and getting outcome $|0\\rangle$, the qubit is now in state:",
            "options": [
                "$\\alpha|0\\rangle + \\beta|1\\rangle$ — superposition is preserved",
                "$|0\\rangle$ — the state collapses",
                "$\\alpha|0\\rangle$ — partial collapse retains the amplitude",
                "An unknown mixed state",
            ],
            "correct_index": 1,
            "explanation": "Measurement causes wave-function collapse. After observing $|0\\rangle$, the state is definitively $|0\\rangle$.",
        },
        {
            "id": "iqc-quiz-q4",
            "concept": "gates",
            "question": "The Hadamard gate $H$ applied to $|1\\rangle$ gives:",
            "options": [
                "$|0\\rangle$",
                "$|1\\rangle$",
                "$\\frac{|0\\rangle + |1\\rangle}{\\sqrt{2}}$",
                "$\\frac{|0\\rangle - |1\\rangle}{\\sqrt{2}}$",
            ],
            "correct_index": 3,
            "explanation": "$H|1\\rangle = \\frac{1}{\\sqrt{2}}\\begin{pmatrix}1&1\\\\1&-1\\end{pmatrix}\\begin{pmatrix}0\\\\1\\end{pmatrix} = \\frac{1}{\\sqrt{2}}\\begin{pmatrix}1\\\\-1\\end{pmatrix} = |-\\rangle$.",
        },
        {
            "id": "iqc-quiz-q5",
            "concept": "normalization",
            "question": "A unitary matrix $U$ must satisfy which condition?",
            "options": [
                "$U^2 = I$",
                "$UU^\\dagger = I$",
                "$U = U^T$",
                "$\\det(U) = 1$",
            ],
            "correct_index": 1,
            "explanation": "By definition, $U$ is unitary iff $UU^\\dagger = U^\\dagger U = I$. This guarantees reversibility and norm preservation.",
        },
    ],

    # ── SQ module quiz ─────────────────────────────────────────────────────────
    "sq-quiz": [
        {
            "id": "sq-quiz-q1",
            "concept": "bloch",
            "question": "On the Bloch sphere, the state $|+\\rangle = \\frac{|0\\rangle + |1\\rangle}{\\sqrt{2}}$ lies at:",
            "options": [
                "The north pole ($\\theta = 0$)",
                "The south pole ($\\theta = \\pi$)",
                "The equator along the $+x$ axis ($\\theta = \\pi/2, \\phi = 0$)",
                "The equator along the $-y$ axis ($\\theta = \\pi/2, \\phi = 3\\pi/2$)",
            ],
            "correct_index": 2,
            "explanation": "$|+\\rangle$ has equal amplitudes with $\\phi = 0$, placing it on the equator at $+x$. North pole = $|0\\rangle$, south pole = $|1\\rangle$.",
        },
        {
            "id": "sq-quiz-q2",
            "concept": "bloch",
            "question": "What are the Bloch coordinates $(x, y, z)$ of the state $|0\\rangle$?",
            "options": [
                "$(0, 0, -1)$",
                "$(1, 0, 0)$",
                "$(0, 0, 1)$",
                "$(0, 1, 0)$",
            ],
            "correct_index": 2,
            "explanation": "For $|0\\rangle = [1, 0]^T$: $z = |\\alpha|^2 - |\\beta|^2 = 1 - 0 = 1$, so $(x,y,z) = (0,0,1)$ — the north pole.",
        },
        {
            "id": "sq-quiz-q3",
            "concept": "gates",
            "question": "Which statement about the $R_x(\\theta)$ gate is correct?",
            "options": [
                "It is a phase gate that only changes the $|1\\rangle$ amplitude",
                "Setting $\\theta = \\pi$ gives the Pauli $X$ gate (up to global phase)",
                "It rotates around the $z$-axis of the Bloch sphere",
                "It creates superposition from $|0\\rangle$ like the Hadamard gate",
            ],
            "correct_index": 1,
            "explanation": "$R_x(\\pi) = -iX$. Since global phases are physically irrelevant, $R_x(\\pi)$ is equivalent to the $X$ gate.",
        },
        {
            "id": "sq-quiz-q4",
            "concept": "gates",
            "question": "Applying $H$ twice to any qubit state $|\\psi\\rangle$ gives:",
            "options": [
                "$|0\\rangle$ always",
                "$H^2|\\psi\\rangle = |\\psi\\rangle$ — the identity",
                "$H^2|\\psi\\rangle = -|\\psi\\rangle$ — a global phase",
                "It depends on the input state",
            ],
            "correct_index": 1,
            "explanation": "$H^2 = I$. The Hadamard is its own inverse: $HH = I$.",
        },
    ],

    # ── MQ module quiz ─────────────────────────────────────────────────────────
    "mq-quiz": [
        {
            "id": "mq-quiz-q1",
            "concept": "entanglement",
            "question": "How is the Bell state $|\\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$ created?",
            "options": [
                "Apply $X$ to both qubits",
                "Apply $H$ to qubit 0, then a CNOT with control=0, target=1",
                "Apply CNOT with control=0, then $H$ to qubit 0",
                "Apply $H$ to both qubits",
            ],
            "correct_index": 1,
            "explanation": "$H|0\\rangle \\otimes |0\\rangle = \\frac{|0\\rangle+|1\\rangle}{\\sqrt{2}}|0\\rangle = \\frac{|00\\rangle+|10\\rangle}{\\sqrt{2}}$. CNOT flips the second qubit when the first is $|1\\rangle$: $\\rightarrow \\frac{|00\\rangle+|11\\rangle}{\\sqrt{2}}$.",
        },
        {
            "id": "mq-quiz-q2",
            "concept": "entanglement",
            "question": "An $n$-qubit system has how many computational basis states?",
            "options": ["$n$", "$2n$", "$n^2$", "$2^n$"],
            "correct_index": 3,
            "explanation": "Each qubit doubles the state space: 1 qubit → 2 states, 2 qubits → 4, $n$ qubits → $2^n$ states.",
        },
        {
            "id": "mq-quiz-q3",
            "concept": "entanglement",
            "question": "Which state is entangled (cannot be written as $|a\\rangle \\otimes |b\\rangle$)?",
            "options": [
                "$|00\\rangle$",
                "$|+\\rangle|0\\rangle = \\frac{|00\\rangle + |10\\rangle}{\\sqrt{2}}$",
                "$\\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$",
                "$|01\\rangle$",
            ],
            "correct_index": 2,
            "explanation": "$\\frac{|00\\rangle+|11\\rangle}{\\sqrt{2}}$ cannot be factored into a product of two single-qubit states — it is the Bell state $|\\Phi^+\\rangle$.",
        },
        {
            "id": "mq-quiz-q4",
            "concept": "entanglement",
            "question": "What does the CNOT gate do to $|10\\rangle$ (control=1, target=0)?",
            "options": ["$|10\\rangle$", "$|11\\rangle$", "$|00\\rangle$", "$|01\\rangle$"],
            "correct_index": 1,
            "explanation": "CNOT flips the target qubit when control is $|1\\rangle$. $|10\\rangle \\rightarrow |11\\rangle$.",
        },
    ],

    # ── DJ module quiz ─────────────────────────────────────────────────────────
    "dj-quiz": [
        {
            "id": "dj-quiz-q1",
            "concept": "algorithms",
            "question": "How many classical queries are needed to determine if a function $f:\\{0,1\\}^n \\rightarrow \\{0,1\\}$ is constant or balanced, in the worst case?",
            "options": ["1", "$n$", "$2^{n-1} + 1$", "$2^n$"],
            "correct_index": 2,
            "explanation": "In the worst case you need $2^{n-1} + 1$ classical queries. With $2^{n-1}$ identical outputs you can't yet distinguish constant from balanced.",
        },
        {
            "id": "dj-quiz-q2",
            "concept": "algorithms",
            "question": "After the Deutsch-Jozsa algorithm measures all $|0\\rangle$ in the input register, the function is:",
            "options": ["Balanced", "Constant", "Cannot be determined", "Neither constant nor balanced"],
            "correct_index": 1,
            "explanation": "If all measured qubits are $|0\\rangle$, the function is constant. Any non-zero measurement indicates balanced.",
        },
        {
            "id": "dj-quiz-q3",
            "concept": "gates",
            "question": "The Deutsch-Jozsa algorithm uses $H^{\\otimes n}$ (Hadamard on all $n$ qubits). This creates:",
            "options": [
                "The state $|0\\rangle^{\\otimes n}$",
                "A uniform superposition of all $2^n$ basis states",
                "The state $|1\\rangle^{\\otimes n}$",
                "An entangled state between all qubits",
            ],
            "correct_index": 1,
            "explanation": "$H^{\\otimes n}|0\\rangle^{\\otimes n} = \\frac{1}{\\sqrt{2^n}}\\sum_{x \\in \\{0,1\\}^n}|x\\rangle$ — an equal superposition of all $2^n$ computational basis states.",
        },
    ],

    # ── Grover module quiz ─────────────────────────────────────────────────────
    "grover-quiz": [
        {
            "id": "grover-quiz-q1",
            "concept": "algorithms",
            "question": "Grover's search algorithm finds a target in an unstructured database of $N$ items in approximately:",
            "options": ["$O(1)$", "$O(\\log N)$", "$O(\\sqrt{N})$", "$O(N)$"],
            "correct_index": 2,
            "explanation": "Grover's algorithm requires $\\approx \\frac{\\pi}{4}\\sqrt{N}$ oracle queries, giving $O(\\sqrt{N})$ complexity — a quadratic speedup over classical $O(N)$.",
        },
        {
            "id": "grover-quiz-q2",
            "concept": "algorithms",
            "question": "The Grover diffusion operator $D = 2|s\\rangle\\langle s| - I$ (where $|s\\rangle$ is the uniform superposition) performs:",
            "options": [
                "A measurement of all qubits",
                "A reflection around the average amplitude",
                "A phase kick-back on the target state only",
                "A Hadamard transform on the ancilla",
            ],
            "correct_index": 1,
            "explanation": "The diffusion operator reflects amplitude vectors around the mean, amplifying the target state's amplitude while suppressing others.",
        },
        {
            "id": "grover-quiz-q3",
            "concept": "algorithms",
            "question": "Over-rotating in Grover's algorithm (too many iterations) will:",
            "options": [
                "Always increase the success probability",
                "Cause the success probability to oscillate and potentially decrease",
                "Have no effect after the optimal iteration count",
                "Immediately collapse the state to the target",
            ],
            "correct_index": 1,
            "explanation": "The target amplitude evolves sinusoidally. After the optimal $\\sim\\sqrt{N}$ iterations, continuing to iterate reduces the success probability.",
        },
    ],
}

# ── Convenience: get quiz by id ────────────────────────────────────────────────

def get_quiz(quiz_id: str) -> list[dict] | None:
    return QUIZ_QUESTIONS.get(quiz_id)

def get_quiz_answer(quiz_id: str, question_id: str) -> int | None:
    questions = QUIZ_QUESTIONS.get(quiz_id, [])
    q = next((q for q in questions if q["id"] == question_id), None)
    return q["correct_index"] if q else None

def score_quiz(quiz_id: str, answers: dict[str, int]) -> dict:
    """
    Score a quiz submission.
    answers: {question_id: chosen_option_index}
    Returns: {score: 0-100, correct: int, total: int, per_question: [...]}
    """
    questions = QUIZ_QUESTIONS.get(quiz_id, [])
    if not questions:
        return {"score": 0, "correct": 0, "total": 0, "per_question": []}

    results = []
    correct_count = 0
    for q in questions:
        chosen = answers.get(q["id"])
        is_correct = chosen == q["correct_index"]
        if is_correct:
            correct_count += 1
        results.append({
            "question_id":   q["id"],
            "concept":       q["concept"],
            "chosen_index":  chosen,
            "correct_index": q["correct_index"],
            "correct":       is_correct,
            "explanation":   q["explanation"] if not is_correct else None,
        })

    score = round((correct_count / len(questions)) * 100) if questions else 0
    return {
        "score":        score,
        "correct":      correct_count,
        "total":        len(questions),
        "passed":       score >= 70,
        "per_question": results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXPANDED curriculum from Xanadu Quantum Codebook source
# Added to MODULE_META, MODULE_ORDER, PATH_META etc.
# ─────────────────────────────────────────────────────────────────────────────

_EXPANDED_MODULE_META: dict[str, dict[str, Any]] = {
    # Path: intro — linear progression
    "qc-states": { "path_id":"intro", "title":"Qubits and Quantum Circuits",            "order":1,
                   "prereq_module_ids": [],
                   "lesson_ids":["qc-1","qc-2"],
                   "codercise_ids":["qc-1-c1","qc-1-c2","qc-2-c1"], "quiz_id":"qc-quiz",
                   "concept_codercises":{"superposition":["qc-1-c1","qc-1-c2"],"gates":["qc-2-c1"]} },
    "sqg":        { "path_id":"intro", "title":"Single-Qubit Gates",                   "order":2,
                   "prereq_module_ids": ["qc-states"],
                   "lesson_ids":["sqg-1","sqg-2","sqg-3"],
                   "codercise_ids":["sqg-1-c1","sqg-1-c2","sqg-2-c1","sqg-3-c1"], "quiz_id":"sqg-quiz",
                   "concept_codercises":{"gates":["sqg-1-c1","sqg-1-c2","sqg-2-c1","sqg-3-c1"]} },
    "univ":       { "path_id":"intro", "title":"Universal Gate Sets",                  "order":3,
                   "prereq_module_ids": ["sqg"],
                   "lesson_ids":["univ-1"],
                   "codercise_ids":["univ-1-c1"], "quiz_id":"univ-quiz",
                   "concept_codercises":{"gates":["univ-1-c1"]} },
    "meas":       { "path_id":"intro", "title":"Measurements and Observables",         "order":4,
                   "prereq_module_ids": ["univ"],
                   "lesson_ids":["meas-1","meas-2"],
                   "codercise_ids":["meas-1-c1","meas-2-c1"], "quiz_id":"meas-quiz",
                   "concept_codercises":{"measurement":["meas-1-c1","meas-2-c1"]} },
    "mqsys":      { "path_id":"intro", "title":"Multi-Qubit Systems & Entanglement",   "order":5,
                   "prereq_module_ids": ["meas"],
                   "lesson_ids":["mqsys-1","mqsys-2","mqsys-3"],
                   "codercise_ids":["mqsys-1-c1","mqsys-2-c1","mqsys-3-c1"], "quiz_id":"mqsys-quiz",
                   "concept_codercises":{"entanglement":["mqsys-2-c1"],"gates":["mqsys-3-c1"]} },
    "teleport":   { "path_id":"intro", "title":"Quantum Teleportation",                "order":6,
                   "prereq_module_ids": ["mqsys"],
                   "lesson_ids":["teleport-1"],
                   "codercise_ids":["teleport-1-c1"], "quiz_id":"teleport-quiz",
                   "concept_codercises":{"entanglement":["teleport-1-c1"]} },
    # Path: algo — requires intro or similar QC foundations
    "oracles":    { "path_id":"algo",  "title":"Superposition, Oracles & Pair Testing","order":1,
                   "prereq_module_ids": [],
                   "lesson_ids":["or-1"],
                   "codercise_ids":["or-1-c1","or-1-c2"], "quiz_id":"or-quiz",
                   "concept_codercises":{"algorithms":["or-1-c1","or-1-c2"]} },
    "dj-full":    { "path_id":"algo",  "title":"Deutsch-Jozsa Algorithm",              "order":2,
                   "prereq_module_ids": ["oracles"],
                   "lesson_ids":["dj-full-1"],
                   "codercise_ids":["dj-full-1-c1","dj-full-1-c2"], "quiz_id":"dj-full-quiz",
                   "concept_codercises":{"algorithms":["dj-full-1-c1","dj-full-1-c2"]} },
    # Path: grover
    "grov-amp":   { "path_id":"grover","title":"Amplitude Amplification",              "order":1,
                   "prereq_module_ids": [],
                   "lesson_ids":["grov-amp-1"],
                   "codercise_ids":["grov-amp-1-c1","grov-amp-1-c2"], "quiz_id":"grov-amp-quiz",
                   "concept_codercises":{"algorithms":["grov-amp-1-c1","grov-amp-1-c2"]} },
    "grov-impl":  { "path_id":"grover","title":"Implementing Grover's Oracle",         "order":2,
                   "prereq_module_ids": ["grov-amp"],
                   "lesson_ids":["grov-impl-1"],
                   "codercise_ids":["grov-impl-1-c1"], "quiz_id":"grov-impl-quiz",
                   "concept_codercises":{"algorithms":["grov-impl-1-c1"]} },
    # Path: hamiltonian
    "ham-basics": { "path_id":"hamiltonian","title":"Hamiltonians and Time Evolution", "order":1,
                   "prereq_module_ids": [],
                   "lesson_ids":["ham-basics-1"],
                   "codercise_ids":["ham-basics-1-c1"], "quiz_id":"ham-basics-quiz",
                   "concept_codercises":{"algorithms":["ham-basics-1-c1"]} },
    "trotterize": { "path_id":"hamiltonian","title":"Trotter-Suzuki Decomposition",    "order":2,
                   "prereq_module_ids": ["ham-basics"],
                   "lesson_ids":["trotterize-1"],
                   "codercise_ids":["trotterize-1-c1"], "quiz_id":"trotterize-quiz",
                   "concept_codercises":{"algorithms":["trotterize-1-c1"]} },
}

MODULE_META.update(_EXPANDED_MODULE_META)

# Rebuild derived lookups after expansion
MODULE_LESSON_TOTALS = { mid: len(m["lesson_ids"]) for mid, m in MODULE_META.items() }
MODULE_CODERCISE_IDS = { mid: m["codercise_ids"] for mid, m in MODULE_META.items() }
MODULE_QUIZ_IDS      = { mid: m["quiz_id"] for mid, m in MODULE_META.items() }
MODULE_PATH          = { mid: m["path_id"] for mid, m in MODULE_META.items() }
MODULE_CONCEPTS      = { mid: list(m["concept_codercises"].keys()) for mid, m in MODULE_META.items() }

# ── Prerequisite lookup (explicit, not inferred from position) ────────────────
MODULE_PREREQS: dict[str, list[str]] = {
    mid: m.get("prereq_module_ids", []) for mid, m in MODULE_META.items()
}

# Lesson ID → module ID reverse map
LESSON_MODULE: dict[str, str] = {}
for _mid, _m in MODULE_META.items():
    for _lid in _m.get("lesson_ids", []):
        LESSON_MODULE[_lid] = _mid
    # Also map quiz lesson IDs
    _qid = _m.get("quiz_id", "")
    if _qid:
        LESSON_MODULE[_qid] = _mid

# Codercise ID → module ID reverse map
CODERCISE_MODULE: dict[str, str] = {}
for _mid, _m in MODULE_META.items():
    for _cid in _m.get("codercise_ids", []):
        CODERCISE_MODULE[_cid] = _mid


def check_module_unlocked(
    module_id: str,
    completed_lesson_ids: set[str],
) -> tuple[bool, list[str]]:
    """
    Return (is_unlocked, missing_prereq_module_ids).

    A module is unlocked when every lesson in every prerequisite module
    has a completed LessonProgress record.

    This is the canonical unlock check — used by all submission endpoints.
    """
    prereqs = MODULE_PREREQS.get(module_id, [])
    missing: list[str] = []

    for prereq_id in prereqs:
        prereq_mod = MODULE_META.get(prereq_id)
        if not prereq_mod:
            continue
        # All content lessons (non-quiz) in the prereq must be completed
        required_lessons = set(prereq_mod.get("lesson_ids", []))
        if not required_lessons.issubset(completed_lesson_ids):
            missing.append(prereq_id)

    return (len(missing) == 0), missing

# Add quiz questions for expanded modules
QUIZ_QUESTIONS.update({
    "qc-quiz": [
        { "id":"qc-q1","concept":"superposition","question":"Which is a valid normalized qubit state?",
          "options":["$|0\\rangle + |1\\rangle$","$\\frac{1}{\\sqrt{2}}|0\\rangle+\\frac{1}{\\sqrt{2}}|1\\rangle$","$0.9|0\\rangle+0.9|1\\rangle$","$2|0\\rangle$"],
          "correct_index":1,"explanation":"$|1/\\sqrt{2}|^2+|1/\\sqrt{2}|^2=1$ ✓"},
        { "id":"qc-q2","concept":"superposition","question":"$\\langle 0|1\\rangle$ equals:",
          "options":["0","1","$1/\\sqrt{2}$","$-1$"],
          "correct_index":0,"explanation":"$|0\\rangle$ and $|1\\rangle$ are orthogonal: $\\langle0|1\\rangle=0$."},
        { "id":"qc-q3","concept":"gates","question":"In PennyLane, quantum functions must:",
          "options":["Return a list of gate names","Apply at least one gate and return a measurement","Import numpy explicitly","Use only unitary matrices"],
          "correct_index":1,"explanation":"A QNode must apply operations and return a measurement such as qml.state(), qml.probs(), or qml.expval()."},
    ],
    "sqg-quiz": [
        { "id":"sqg-q1","concept":"gates","question":"$X|0\\rangle$ equals:",
          "options":["$|0\\rangle$","$|1\\rangle$","$|+\\rangle$","$-|0\\rangle$"],
          "correct_index":1,"explanation":"Pauli X is the quantum NOT gate: $X|0\\rangle=|1\\rangle$."},
        { "id":"sqg-q2","concept":"gates","question":"$Z|+\\rangle$ where $|+\\rangle=\\frac{|0\\rangle+|1\\rangle}{\\sqrt{2}}$ equals:",
          "options":["$|+\\rangle$","$|−\\rangle=\\frac{|0\\rangle-|1\\rangle}{\\sqrt{2}}$","$|0\\rangle$","$-|+\\rangle$"],
          "correct_index":1,"explanation":"$Z|+\\rangle=\\frac{Z|0\\rangle+Z|1\\rangle}{\\sqrt{2}}=\\frac{|0\\rangle-|1\\rangle}{\\sqrt{2}}=|−\\rangle$."},
        { "id":"sqg-q3","concept":"gates","question":"Which PennyLane function returns the full state vector?",
          "options":["qml.probs()","qml.expval()","qml.state()","qml.sample()"],
          "correct_index":2,"explanation":"qml.state() returns the full complex state vector of the system."},
        { "id":"sqg-q4","concept":"gates","question":"$R_X(\\pi)|0\\rangle$ produces (up to global phase):",
          "options":["$|0\\rangle$","$|1\\rangle$","$|+\\rangle$","$|−\\rangle$"],
          "correct_index":1,"explanation":"$R_X(\\pi)=-iX$, so $R_X(\\pi)|0\\rangle=-i|1\\rangle\\equiv|1\\rangle$ up to global phase."},
    ],
    "univ-quiz": [
        { "id":"univ-q1","concept":"gates","question":"Any single-qubit gate can be written as $e^{i\\alpha}R_Z(\\omega)R_Y(\\theta)R_Z(\\phi)$. How many real parameters are needed?",
          "options":["2","3","4","8"],
          "correct_index":2,"explanation":"Four real parameters: global phase $\\alpha$ plus Euler angles $\\omega,\\theta,\\phi$."},
        { "id":"univ-q2","concept":"gates","question":"The set $\\{H, T\\}$ is:",
          "options":["Not universal","Universal for all single-qubit gates exactly","Approximately universal (dense in SU(2))","Only useful for phase gates"],
          "correct_index":2,"explanation":"$\\{H,T\\}$ generates a group that is dense in SU(2) — any single-qubit gate can be approximated arbitrarily well."},
    ],
    "meas-quiz": [
        { "id":"meas-q1","concept":"measurement","question":"The probability of measuring $|\\phi\\rangle$ from state $|\\psi\\rangle$ is:",
          "options":["$\\langle\\phi|\\psi\\rangle$","$|\\langle\\phi|\\psi\\rangle|^2$","$\\langle\\psi|\\phi\\rangle$","$|\\psi\\rangle\\langle\\phi|$"],
          "correct_index":1,"explanation":"Born rule: $\\Pr(\\phi)=|\\langle\\phi|\\psi\\rangle|^2$."},
        { "id":"meas-q2","concept":"measurement","question":"$\\langle Z\\rangle$ for state $|+\\rangle$ equals:",
          "options":["$+1$","$-1$","$0$","$1/\\sqrt{2}$"],
          "correct_index":2,"explanation":"$|+\\rangle=(|0\\rangle+|1\\rangle)/\\sqrt{2}$. $\\langle Z\\rangle=|\\alpha|^2-|\\beta|^2=1/2-1/2=0$."},
        { "id":"meas-q3","concept":"measurement","question":"To measure in the X basis $\\{|+\\rangle,|−\\rangle\\}$ using a computational basis measurement:",
          "options":["Apply Z then measure","Apply H then measure","Measure directly","Apply X then measure"],
          "correct_index":1,"explanation":"Applying H rotates the X basis to the Z basis. Measuring after H gives X-basis outcomes."},
    ],
    "mqsys-quiz": [
        { "id":"mqsys-q1","concept":"entanglement","question":"How many computational basis states does a 4-qubit system have?",
          "options":["4","8","16","32"],
          "correct_index":2,"explanation":"$2^4=16$ basis states for 4 qubits."},
        { "id":"mqsys-q2","concept":"entanglement","question":"$\\text{CNOT}|10\\rangle$ gives:",
          "options":["$|10\\rangle$","$|11\\rangle$","$|00\\rangle$","$|01\\rangle$"],
          "correct_index":1,"explanation":"Control=1 so target flips: $|10\\rangle\\to|11\\rangle$."},
        { "id":"mqsys-q3","concept":"entanglement","question":"Which state is entangled?",
          "options":["$|00\\rangle$","$|+\\rangle|0\\rangle$","$\\frac{|00\\rangle+|11\\rangle}{\\sqrt{2}}$","$|1\\rangle|+\\rangle$"],
          "correct_index":2,"explanation":"The Bell state $|\\Phi^+\\rangle$ cannot be written as a product of two single-qubit states."},
    ],
    "teleport-quiz": [
        { "id":"teleport-q1","concept":"entanglement","question":"The no-cloning theorem states:",
          "options":["Quantum states cannot be measured","Quantum states cannot be copied exactly","Entangled states collapse upon measurement","You cannot prepare |0> from |1>"],
          "correct_index":1,"explanation":"It is impossible to create an exact copy of an arbitrary unknown quantum state."},
        { "id":"teleport-q2","concept":"entanglement","question":"Quantum teleportation requires:",
          "options":["A faster-than-light channel","One pre-shared entangled pair and 2 classical bits","Three quantum channels","No measurement"],
          "correct_index":1,"explanation":"Teleportation uses one Bell pair (pre-shared entanglement) and sends 2 classical bits from Alice to Bob."},
    ],
    "or-quiz": [
        { "id":"or-q1","concept":"algorithms","question":"A phase oracle $U_f$ acts on $|x\\rangle$ as:",
          "options":["$|x\\oplus f(x)\\rangle$","$(-1)^{f(x)}|x\\rangle$","$f(x)|x\\rangle$","$|x\\rangle+|f(x)\\rangle$"],
          "correct_index":1,"explanation":"The phase oracle encodes $f$ as a phase: $U_f|x\\rangle=(-1)^{f(x)}|x\\rangle$."},
        { "id":"or-q2","concept":"algorithms","question":"After applying a phase oracle to the uniform superposition, the measurement probabilities:",
          "options":["All become zero except the solution","All remain equal to 1/N","The solution probability doubles","All become 1"],
          "correct_index":1,"explanation":"Phase flips do not change probabilities — only amplitudes. You need multiple operations (Grover steps) to change the probability distribution."},
    ],
    "dj-full-quiz": [
        { "id":"dj-q1","concept":"algorithms","question":"In Deutsch-Jozsa, observing $|0\\rangle^{\\otimes n}$ at the output means the function is:",
          "options":["Balanced","Constant","Unknown","Bijective"],
          "correct_index":1,"explanation":"If $f$ is constant, $\\mathcal{A}_{\\mathbf{0}}=\\pm 1$, so $|\\mathbf{0}\\rangle$ is always observed."},
        { "id":"dj-q2","concept":"algorithms","question":"The Deutsch-Jozsa algorithm determines balanced vs constant with how many oracle calls?",
          "options":["$2^{n-1}+1$","$n$","$1$","$\\sqrt{2^n}$"],
          "correct_index":2,"explanation":"DJ uses exactly one oracle call — the key quantum advantage over the classical $2^{n-1}+1$ worst case."},
    ],
    "grov-amp-quiz": [
        { "id":"grov-amp-q1","concept":"algorithms","question":"The diffusion operator $D=2|\\psi\\rangle\\langle\\psi|-I$ applied to $|\\psi\\rangle$ gives:",
          "options":["$-|\\psi\\rangle$","$|\\psi\\rangle$","$0$","$2|\\psi\\rangle$"],
          "correct_index":1,"explanation":"$D|\\psi\\rangle=2\\langle\\psi|\\psi\\rangle|\\psi\\rangle-|\\psi\\rangle=2|\\psi\\rangle-|\\psi\\rangle=|\\psi\\rangle$."},
        { "id":"grov-amp-q2","concept":"algorithms","question":"The optimal number of Grover iterations for $N$ items is approximately:",
          "options":["$N/4$","$\\sqrt{N}$","$\\pi\\sqrt{N}/4$","$\\log N$"],
          "correct_index":2,"explanation":"The optimal step count is $S\\approx\\frac{\\pi}{4}\\sqrt{N}$."},
    ],
    "grov-impl-quiz": [
        { "id":"grov-impl-q1","concept":"algorithms","question":"Phase kickback using an auxiliary qubit in $|−\\rangle$ requires:",
          "options":["An additional Hadamard at the end","The target qubit in $|1\\rangle$","Initializing aux in $|−\\rangle=(|0\\rangle-|1\\rangle)/\\sqrt{2}$ and applying a conditional X","Running the circuit twice"],
          "correct_index":2,"explanation":"With aux in $|−\\rangle$, a CNOT flipping aux when $x=s$ kicks a $-1$ phase back onto $|s\\rangle$ in the query register."},
    ],
    "ham-basics-quiz": [
        { "id":"ham-basics-q1","concept":"algorithms","question":"The time evolution operator for Hamiltonian $\\hat{H}$ is:",
          "options":["$e^{\\hat{H}t}$","$e^{-i\\hat{H}t/\\hbar}$","$\\hat{H}^t$","$\\cos(\\hat{H}t)$"],
          "correct_index":1,"explanation":"Schrödinger equation gives $U(t)=e^{-i\\hat{H}t/\\hbar}$."},
        { "id":"ham-basics-q2","concept":"algorithms","question":"For a single electron in a $z$-directed magnetic field, $U(t)=e^{i\\alpha t Z}$ is equivalent to which PennyLane gate?",
          "options":["qml.PauliX","qml.Hadamard","qml.RZ","qml.CNOT"],
          "correct_index":2,"explanation":"$R_Z(\\theta)=e^{-i\\theta Z/2}$, so $e^{i\\alpha t Z}=R_Z(-2\\alpha t)$."},
    ],
    "trotterize-quiz": [
        { "id":"trotterize-q1","concept":"algorithms","question":"The Trotter-Suzuki formula approximates $e^{(A+B)t}$ as:",
          "options":["$e^{At}e^{Bt}$","$(e^{At/n}e^{Bt/n})^n$ for large $n$","$e^{ABt}$","$e^{At}+e^{Bt}-I$"],
          "correct_index":1,"explanation":"$e^{(A+B)t}\\approx(e^{At/n}e^{Bt/n})^n$ with error $O(1/n)$ for large $n$."},
        { "id":"trotterize-q2","concept":"algorithms","question":"When does $e^{A+B}=e^Ae^B$ hold exactly?",
          "options":["Always","Never","When $[A,B]=AB-BA=0$ (operators commute)","When $A=B$"],
          "correct_index":2,"explanation":"The exponential law holds exactly when $A$ and $B$ commute."},
    ],
})

# Rebuild path-level facts after expansion
_EXPANDED_PATH_META: dict[str, dict[str, Any]] = {
    "intro":       { "title": "Introduction to Quantum Computing",
                     "modules": ["qc-states","sqg","univ","meas","mqsys","teleport"] },
    "algo":        { "title": "Introduction to Quantum Algorithms",
                     "modules": ["oracles","dj-full"] },
    "grover":      { "title": "Grover's Search Algorithm",
                     "modules": ["grov-amp","grov-impl"] },
    "hamiltonian": { "title": "Hamiltonian Simulation",
                     "modules": ["ham-basics","trotterize"] },
}
PATH_META.update(_EXPANDED_PATH_META)

def _all_ids_updated(path_id: str, key: str) -> list[str]:
    result = []
    for mid in PATH_META[path_id]["modules"]:
        result.extend(MODULE_META[mid].get(key, []))
    return result

for pid in _EXPANDED_PATH_META:
    PATH_ALL_LESSON_IDS[pid]    = _all_ids_updated(pid, "lesson_ids")
    PATH_ALL_CODERCISE_IDS[pid] = _all_ids_updated(pid, "codercise_ids")
    PATH_ALL_QUIZ_IDS[pid]      = [MODULE_META[mid]["quiz_id"] for mid in PATH_META[pid]["modules"]]

# Certification requirements for new paths
CERT_REQUIREMENTS.update({
    "intro": {
        "path_title":          "Introduction to Quantum Computing",
        "required_lessons":    len(PATH_ALL_LESSON_IDS["intro"]),
        "required_codercises": len(PATH_ALL_CODERCISE_IDS["intro"]),
        "required_quizzes":    4,
        "passing_quiz_score":  70,
        "total_quizzes":       len(PATH_ALL_QUIZ_IDS["intro"]),
        "lesson_ids":          PATH_ALL_LESSON_IDS["intro"],
        "codercise_ids":       PATH_ALL_CODERCISE_IDS["intro"],
        "quiz_ids":            PATH_ALL_QUIZ_IDS["intro"],
    },
    "algo": {
        "path_title":          "Introduction to Quantum Algorithms",
        "required_lessons":    len(PATH_ALL_LESSON_IDS["algo"]),
        "required_codercises": len(PATH_ALL_CODERCISE_IDS["algo"]),
        "required_quizzes":    1,
        "passing_quiz_score":  70,
        "total_quizzes":       len(PATH_ALL_QUIZ_IDS["algo"]),
        "lesson_ids":          PATH_ALL_LESSON_IDS["algo"],
        "codercise_ids":       PATH_ALL_CODERCISE_IDS["algo"],
        "quiz_ids":            PATH_ALL_QUIZ_IDS["algo"],
    },
    "grover": {
        "path_title":          "Grover's Search Algorithm",
        "required_lessons":    len(PATH_ALL_LESSON_IDS["grover"]),
        "required_codercises": len(PATH_ALL_CODERCISE_IDS["grover"]),
        "required_quizzes":    1,
        "passing_quiz_score":  70,
        "total_quizzes":       len(PATH_ALL_QUIZ_IDS["grover"]),
        "lesson_ids":          PATH_ALL_LESSON_IDS["grover"],
        "codercise_ids":       PATH_ALL_CODERCISE_IDS["grover"],
        "quiz_ids":            PATH_ALL_QUIZ_IDS["grover"],
    },
    "hamiltonian": {
        "path_title":          "Hamiltonian Simulation",
        "required_lessons":    len(PATH_ALL_LESSON_IDS["hamiltonian"]),
        "required_codercises": len(PATH_ALL_CODERCISE_IDS["hamiltonian"]),
        "required_quizzes":    1,
        "passing_quiz_score":  70,
        "total_quizzes":       len(PATH_ALL_QUIZ_IDS["hamiltonian"]),
        "lesson_ids":          PATH_ALL_LESSON_IDS["hamiltonian"],
        "codercise_ids":       PATH_ALL_CODERCISE_IDS["hamiltonian"],
        "quiz_ids":            PATH_ALL_QUIZ_IDS["hamiltonian"],
    },
})

# Rebuild CODERCISE_CONCEPT map with expanded modules
CODERCISE_CONCEPT.update({
    "qc-1-c1":"superposition","qc-1-c2":"superposition","qc-2-c1":"gates",
    "sqg-1-c1":"gates","sqg-1-c2":"gates","sqg-2-c1":"gates","sqg-3-c1":"measurement",
    "univ-1-c1":"gates",
    "meas-1-c1":"measurement","meas-2-c1":"measurement",
    "mqsys-1-c1":"entanglement","mqsys-2-c1":"entanglement","mqsys-3-c1":"gates",
    "teleport-1-c1":"entanglement",
    "or-1-c1":"algorithms","or-1-c2":"algorithms",
    "dj-full-1-c1":"algorithms","dj-full-1-c2":"algorithms",
    "grov-amp-1-c1":"algorithms","grov-amp-1-c2":"algorithms",
    "grov-impl-1-c1":"algorithms",
    "ham-basics-1-c1":"algorithms",
    "trotterize-1-c1":"algorithms",
})

# Rebuild MODULE_ORDER to include expanded modules after existing ones
MODULE_ORDER = [
    "iqc","sq","mq","qalgo-dj","qalgo-grover",
    "qc-states","sqg","univ","meas","mqsys","teleport",
    "oracles","dj-full",
    "grov-amp","grov-impl",
    "ham-basics","trotterize",
]



"""
Adaptive learning state API.

All mastery values are DERIVED from existing records — no duplication:
  - Module mastery  ← LessonProgress
  - Codercise mastery ← CodeSubmission
  - Concept mastery ← ConceptAnswer + CodeSubmission (via CODERCISE_CONCEPT map)
  - Quiz performance ← QuizSubmission (best score per quiz)
  - Recommendation  ← deterministic 3-rule engine (see _compute_recommendation)

GET  /adaptive/state   — full adaptive state for the current user
POST /adaptive/concept — record a single concept answer from quiz/assessment

Structural constants (module ids, lesson counts, codercise ids, concepts) are
imported from curriculum_meta — never hardcoded here.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, Field as SQLField
from sqlmodel import SQLModel
from pydantic import BaseModel

from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.progress import LessonProgress, CodeSubmission, QuizSubmission

# ── All structural constants come from curriculum_meta ────────────────────────
from app.services.curriculum_meta import (
    MODULE_META,
    MODULE_ORDER,
    MODULE_PATH,
    MODULE_LESSON_TOTALS,
    MODULE_CONCEPTS,
    CODERCISE_CONCEPT,
    CERT_REQUIREMENTS,
)

router = APIRouter(prefix="/adaptive", tags=["adaptive"])

CONCEPT_LABELS = {
    "superposition": "Superposition",
    "normalization": "State Normalization",
    "gates":         "Quantum Gates",
    "measurement":   "Measurement",
    "entanglement":  "Entanglement",
    "algorithms":    "Quantum Algorithms",
    "bloch":         "Bloch Sphere",
}


# ── Mastery helpers ────────────────────────────────────────────────────────────

def _mastery_level(correct: int, total: int, streak: int = 0) -> str:
    if total == 0:
        return "not_started"
    accuracy = correct / total
    if total >= 5 and accuracy >= 0.9 and streak >= 3:
        return "mastered"
    if total >= 3 and accuracy >= 0.75:
        return "proficient"
    if total >= 2 and accuracy >= 0.5:
        return "practiced"
    return "learning"


# ── Recommendation engine ──────────────────────────────────────────────────────

def _compute_recommendation(
    completed_modules: set,
    concept_mastery: dict,
    weak_concepts: list,
    quiz_performance: dict,  # quiz_id → {passed, score}
) -> dict:
    """
    Deterministic, explainable next-step recommendation.

    Rules (checked in order):
      1. Completed module has a quiz that was attempted but not passed → retake quiz
      2. Completed module has weak concepts from practice → revisit module
      3. Incomplete module with prerequisite satisfied and weak concepts → prioritise
      4. Default: first incomplete unlocked module
    """

    # Rule 1: failed quiz on a completed module
    for module_id in MODULE_ORDER:
        if module_id not in completed_modules:
            continue
        quiz_id = MODULE_META[module_id]["quiz_id"]
        qp = quiz_performance.get(quiz_id)
        if qp and not qp["passed"]:
            return {
                "module_id": module_id,
                "action":    "retake_quiz",
                "reason":    f"You scored {qp['score']}% on the {MODULE_META[module_id]['title']} quiz. Retake it to strengthen your understanding.",
            }

    # Rule 2: completed module has weak concepts from codercise practice
    for module_id in MODULE_ORDER:
        if module_id not in completed_modules:
            continue
        concepts = MODULE_CONCEPTS.get(module_id, [])
        weak_here = [
            c for c in concepts
            if concept_mastery.get(c, {}).get("mastery") == "learning"
            and concept_mastery.get(c, {}).get("attempt_count", 0) >= 2
        ]
        if weak_here:
            names = " and ".join(CONCEPT_LABELS.get(c, c) for c in weak_here[:2])
            return {
                "module_id": module_id,
                "action":    "revisit",
                "reason":    f"You struggled with {names}. Revisiting this module will strengthen your foundation.",
            }

    # Rule 3: first unlocked incomplete module whose concepts overlap with weak list
    for module_id in MODULE_ORDER:
        if module_id in completed_modules:
            continue
        idx = MODULE_ORDER.index(module_id)
        prereq_done = idx == 0 or MODULE_ORDER[idx - 1] in completed_modules
        if not prereq_done:
            continue
        concepts = MODULE_CONCEPTS.get(module_id, [])
        weak_here = [c for c in concepts if c in weak_concepts]
        if weak_here:
            names = " and ".join(CONCEPT_LABELS.get(c, c) for c in weak_here[:2])
            return {
                "module_id": module_id,
                "action":    "start",
                "reason":    f"Your assessment flagged {names} as needing attention — this module covers exactly that.",
            }

    # Rule 4: first incomplete unlocked module
    for module_id in MODULE_ORDER:
        if module_id in completed_modules:
            continue
        idx = MODULE_ORDER.index(module_id)
        prereq_done = idx == 0 or MODULE_ORDER[idx - 1] in completed_modules
        if prereq_done:
            return {
                "module_id": module_id,
                "action":    "start",
                "reason":    "This is your next step on the learning path.",
            }

    return {"module_id": None, "action": "complete", "reason": "All modules complete — outstanding work!"}


# ── ConceptAnswer table (answers from quizzes and assessments) ─────────────────

class ConceptAnswer(SQLModel, table=True):
    __tablename__ = "concept_answers"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="users.id", index=True)
    concept: str = SQLField(index=True)
    correct: bool
    source: str = "quiz"
    answered_at: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))


# ── Request/response models ────────────────────────────────────────────────────

class ConceptAnswerIn(BaseModel):
    concept: str
    correct: bool
    source: str = "quiz"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/concept")
async def record_concept_answer(
    data: ConceptAnswerIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Persist a concept answer from a quiz, assessment, or placement test."""
    row = ConceptAnswer(
        user_id=current_user.id,
        concept=data.concept,
        correct=data.correct,
        source=data.source,
    )
    session.add(row)
    await session.commit()
    return {"status": "ok"}


@router.get("/state")
async def get_adaptive_state(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Return full adaptive state derived from DB records:
      - module mastery      ← LessonProgress
      - codercise mastery   ← CodeSubmission
      - concept mastery     ← ConceptAnswer + CodeSubmission
      - quiz performance    ← QuizSubmission (best per quiz)
      - recommendation      ← deterministic engine
    """
    uid = current_user.id

    # ── Module mastery (LessonProgress) ──────────────────────────────────────
    lp_result = await session.exec(
        select(LessonProgress).where(
            LessonProgress.user_id == uid,
            LessonProgress.completed == True,
        )
    )
    completed_lps = lp_result.all()

    module_completions: dict[str, int] = {}
    for lp in completed_lps:
        module_completions[lp.module_id] = module_completions.get(lp.module_id, 0) + 1

    completed_modules: set[str] = set()
    module_mastery: dict[str, dict] = {}
    for module_id, total in MODULE_LESSON_TOTALS.items():
        done = module_completions.get(module_id, 0)
        if done >= total:
            completed_modules.add(module_id)
        mastery = (
            "mastered"   if done >= total and total > 0 else
            "practiced"  if done > 0 else
            "not_started"
        )
        module_mastery[module_id] = {
            "module_id":         module_id,
            "path_id":           MODULE_PATH.get(module_id, "fqc"),
            "mastery_level":     mastery,
            "lessons_completed": done,
            "lessons_total":     total,
        }

    # ── Codercise pass stats (CodeSubmission) ─────────────────────────────────
    cs_result = await session.exec(
        select(CodeSubmission).where(CodeSubmission.user_id == uid)
    )
    submissions = cs_result.all()

    codercise_stats: dict[str, dict] = {}
    for sub in submissions:
        s = codercise_stats.setdefault(sub.codercise_id, {"passed": 0, "total": 0, "latest_passed": False})
        s["total"] += 1
        if sub.passed:
            s["passed"] += 1
            s["latest_passed"] = True
    codercises_passed_total = sum(1 for s in codercise_stats.values() if s["latest_passed"])

    # ── Quiz performance (QuizSubmission) ─────────────────────────────────────
    qs_result = await session.exec(
        select(QuizSubmission).where(QuizSubmission.user_id == uid)
    )
    quiz_rows = qs_result.all()

    quiz_performance: dict[str, dict] = {}
    for row in quiz_rows:
        existing = quiz_performance.get(row.quiz_id)
        if existing is None or row.score > existing["score"]:
            quiz_performance[row.quiz_id] = {
                "quiz_id":    row.quiz_id,
                "module_id":  row.module_id,
                "score":      row.score,
                "passed":     row.passed,
            }

    # ── Concept mastery (ConceptAnswer + inferred from CodeSubmission) ─────────
    ca_result = await session.exec(
        select(ConceptAnswer).where(ConceptAnswer.user_id == uid)
    )
    concept_rows = ca_result.all()

    concept_counts: dict[str, dict] = {}

    # Infer from codercise results
    for sub in submissions:
        concept = CODERCISE_CONCEPT.get(sub.codercise_id)
        if concept:
            c = concept_counts.setdefault(concept, {"correct": 0, "total": 0, "streak": 0})
            c["total"] += 1
            if sub.passed:
                c["correct"] += 1
                c["streak"] += 1
            else:
                c["streak"] = 0

    # Infer from quiz submissions (per-question concept tags)
    # QuizSubmission only has aggregate score; per-question concept data
    # comes from ConceptAnswer rows recorded during quiz submission.
    for row in concept_rows:
        c = concept_counts.setdefault(row.concept, {"correct": 0, "total": 0, "streak": 0})
        c["total"] += 1
        if row.correct:
            c["correct"] += 1
            c["streak"] += 1
        else:
            c["streak"] = 0

    concept_mastery: dict[str, dict] = {}
    for concept, counts in concept_counts.items():
        mastery = _mastery_level(counts["correct"], counts["total"], counts.get("streak", 0))
        concept_mastery[concept] = {
            "concept":       concept,
            "mastery":       mastery,
            "correct_count": counts["correct"],
            "attempt_count": counts["total"],
            "streak":        counts.get("streak", 0),
        }

    weak_concepts = [
        c for c, m in concept_mastery.items()
        if m["mastery"] in ("learning",) and m["attempt_count"] > 0
    ]
    strong_concepts = [
        c for c, m in concept_mastery.items()
        if m["mastery"] in ("proficient", "mastered")
    ]

    # ── Recommendation ─────────────────────────────────────────────────────────
    recommendation = _compute_recommendation(
        completed_modules, concept_mastery, weak_concepts, quiz_performance
    )

    return {
        "module_mastery":          module_mastery,
        "concept_mastery":         concept_mastery,
        "weak_concepts":           weak_concepts,
        "strong_concepts":         strong_concepts,
        "recommendation":          recommendation,
        "quiz_performance":        quiz_performance,
        "codercises_passed":       codercises_passed_total,
        "codercise_stats":         codercise_stats,
        "completed_lessons_count": len(completed_lps),
    }

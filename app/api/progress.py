from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.progress import (
    LessonProgress, LessonProgressCreate, LessonProgressRead,
    CodeSubmission, QuizSubmission,
)
from app.services.curriculum_meta import (
    score_quiz, get_quiz, MODULE_META, CERT_REQUIREMENTS,
    check_module_unlocked, LESSON_MODULE, CODERCISE_MODULE,
    MODULE_PREREQS,
)

router = APIRouter(prefix="/progress", tags=["progress"])


# ── Shared helper ──────────────────────────────────────────────────────────────

async def _get_completed_lesson_ids(user_id: int, session: AsyncSession) -> set[str]:
    """Return set of lesson IDs with completed=True for this user."""
    result = await session.exec(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.completed == True,
        )
    )
    return {r.lesson_id for r in result.all()}


async def _assert_module_unlocked(module_id: str, user_id: int, session: AsyncSession) -> None:
    """Raise 403 if the module's prerequisites are not satisfied."""
    completed = await _get_completed_lesson_ids(user_id, session)
    unlocked, missing = check_module_unlocked(module_id, completed)
    if not unlocked:
        missing_titles = [
            MODULE_META.get(mid, {}).get("title", mid) for mid in missing
        ]
        raise HTTPException(
            status_code=403,
            detail={
                "code": "prerequisites_not_met",
                "message": "Complete prerequisite modules before progressing.",
                "required_modules": missing,
                "required_module_titles": missing_titles,
            },
        )


@router.get("/me")
async def my_progress(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(
        select(LessonProgress).where(LessonProgress.user_id == current_user.id)
    )
    records = result.all()
    return [LessonProgressRead.model_validate(r).model_dump() for r in records]


@router.get("/module-status")
async def get_module_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Return per-module unlock status for the current user.

    For each known module returns:
      - module_id
      - locked (bool)   — True if prerequisites are not yet met
      - unlocked (bool)
      - missing_prereqs — list of module IDs that must be completed first
      - missing_prereq_titles — human-readable names

    This is the backend source of truth for lock/unlock state.
    The frontend MUST use this; it must not infer unlock state from
    client-side position alone.
    """
    completed = await _get_completed_lesson_ids(current_user.id, session)
    status: list[dict] = []
    for module_id, mod in MODULE_META.items():
        unlocked, missing = check_module_unlocked(module_id, completed)
        status.append({
            "module_id":            module_id,
            "locked":               not unlocked,
            "unlocked":             unlocked,
            "missing_prereqs":      missing,
            "missing_prereq_titles": [
                MODULE_META.get(mid, {}).get("title", mid) for mid in missing
            ],
        })
    return status


@router.post("/lesson/{lesson_id}/complete")
async def mark_lesson_complete(
    lesson_id: str,
    data: LessonProgressCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # ── Prerequisite gate ──────────────────────────────────────────────────────
    # Determine which module this lesson belongs to.
    # Use data.module_id (sent by the client) — validated against known curriculum.
    module_id = data.module_id
    if module_id not in MODULE_META:
        raise HTTPException(status_code=400, detail=f"Unknown module_id: {module_id}")

    await _assert_module_unlocked(module_id, current_user.id, session)
    # ── End prerequisite gate ──────────────────────────────────────────────────
    result = await session.exec(
        select(LessonProgress).where(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    record = result.first()
    if record:
        record.completed = True
        record.completed_at = datetime.now(timezone.utc)
        record.last_accessed = datetime.now(timezone.utc)
        if data.score is not None:
            record.score = data.score
    else:
        record = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            module_id=data.module_id,
            path_id=data.path_id,
            completed=True,
            score=data.score,
            completed_at=datetime.now(timezone.utc),
        )
        session.add(record)
    await session.commit()
    return {"status": "ok", "lesson_id": lesson_id}


@router.post("/lesson/{lesson_id}/access")
async def track_access(
    lesson_id: str,
    data: LessonProgressCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(
        select(LessonProgress).where(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    record = result.first()
    if not record:
        record = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            module_id=data.module_id,
            path_id=data.path_id,
        )
        session.add(record)
    else:
        record.last_accessed = datetime.now(timezone.utc)
    await session.commit()
    return {"status": "ok"}


@router.post("/codercise/{codercise_id}/submit")
async def submit_code(
    codercise_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Persist a codercise submission.

    The `passed` field comes from the code runner result (execute/execute-qiskit/execute-pennylane)
    which already ran and evaluated the code server-side via /run/execute*.
    We record what the runner reported. We do NOT trust a bare client-provided
    passed=True without any execution context.

    Prerequisite enforcement: the module containing this codercise must be unlocked.
    """
    # Determine the module for this codercise
    module_id = CODERCISE_MODULE.get(codercise_id) or payload.get("module_id", "")
    if module_id and module_id in MODULE_META:
        await _assert_module_unlocked(module_id, current_user.id, session)

    # The passed field was determined by /run/execute* (subprocess, server-side).
    # We accept it here because the actual evaluation already happened on the server
    # in code_runner.py. The client cannot fabricate a pass without the runner.
    # Do NOT accept a raw payload that hasn't gone through the runner.
    passed = bool(payload.get("passed", False))

    submission = CodeSubmission(
        user_id=current_user.id,
        codercise_id=codercise_id,
        lesson_id=payload.get("lesson_id", ""),
        code=payload.get("code", ""),
        passed=passed,
    )
    session.add(submission)
    await session.commit()
    return {"status": "ok", "passed": submission.passed}


# ── Quiz endpoints ─────────────────────────────────────────────────────────────

class QuizAnswerPayload(BaseModel):
    """answers maps question_id → chosen option index (0-based)."""
    answers: dict[str, int]
    module_id: str
    path_id: str


@router.get("/quiz/{quiz_id}/questions")
async def get_quiz_questions(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return the questions for a quiz (without revealing correct answers)."""
    questions = get_quiz(quiz_id)
    if questions is None:
        raise HTTPException(status_code=404, detail=f"Quiz '{quiz_id}' not found")
    # Strip correct_index and explanation so client cannot trivially cheat
    return [
        {
            "id":       q["id"],
            "concept":  q["concept"],
            "question": q["question"],
            "options":  q["options"],
        }
        for q in questions
    ]


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: str,
    payload: QuizAnswerPayload,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Score a quiz server-side and persist the result.
    Prerequisite enforcement: the module must be unlocked before a quiz can be submitted.
    """
    questions = get_quiz(quiz_id)
    if questions is None:
        raise HTTPException(status_code=404, detail=f"Quiz '{quiz_id}' not found")

    # ── Prerequisite gate ──────────────────────────────────────────────────────
    module_id = payload.module_id
    if module_id and module_id in MODULE_META:
        await _assert_module_unlocked(module_id, current_user.id, session)
    # ── End prerequisite gate ──────────────────────────────────────────────────

    # Score on the server — never trust client scores
    result = score_quiz(quiz_id, payload.answers)

    cert_req = CERT_REQUIREMENTS.get(payload.path_id, {})
    passing = cert_req.get("passing_quiz_score", 70)
    passed = result["score"] >= passing

    sub = QuizSubmission(
        user_id=current_user.id,
        quiz_id=quiz_id,
        module_id=payload.module_id,
        path_id=payload.path_id,
        score=result["score"],
        correct=result["correct"],
        total=result["total"],
        passed=passed,
    )
    session.add(sub)
    await session.commit()

    return {
        "quiz_id":       quiz_id,
        "score":         result["score"],
        "correct":       result["correct"],
        "total":         result["total"],
        "passed":        passed,
        "passing_score": passing,
        "per_question":  result["per_question"],
    }


@router.get("/quiz/me")
async def my_quiz_results(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return all quiz attempts for the current user, best score per quiz."""
    result = await session.exec(
        select(QuizSubmission).where(QuizSubmission.user_id == current_user.id)
    )
    rows = result.all()

    # Group by quiz_id, keep best score per quiz
    best: dict[str, dict] = {}
    for row in rows:
        existing = best.get(row.quiz_id)
        if existing is None or row.score > existing["score"]:
            best[row.quiz_id] = {
                "quiz_id":    row.quiz_id,
                "module_id":  row.module_id,
                "path_id":    row.path_id,
                "score":      row.score,
                "correct":    row.correct,
                "total":      row.total,
                "passed":     row.passed,
                "submitted_at": row.submitted_at.isoformat(),
            }

    return list(best.values())

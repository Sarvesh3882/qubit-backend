"""
Certification API.

GET  /certification/eligibility/{path_id}  — detailed requirements + progress
POST /certification/issue                   — issue a certificate (idempotent)
GET  /certification/{cert_id}              — public verification (no auth required)
GET  /certification/me                     — list all certs for current user

All requirement rules come from curriculum_meta.CERT_REQUIREMENTS.
Eligibility is derived purely from database records — client booleans are never trusted.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel

from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.progress import LessonProgress, CodeSubmission, QuizSubmission
from app.models.adaptive import Certificate, CertificateRead

# ── Single source of truth for certification rules ────────────────────────────
from app.services.curriculum_meta import CERT_REQUIREMENTS

router = APIRouter(prefix="/certification", tags=["certification"])


def _generate_cert_id(path_id: str, user_id: int) -> str:
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    hex_part = format(abs(hash(f"{user_id}-{path_id}")) % 0xFFFF, "04X")
    return f"QUBIT-{path_id.upper()}-{date}-{hex_part}"


async def _check_eligibility(
    user_id: int,
    path_id: str,
    session: AsyncSession,
) -> dict:
    """
    Compute certification eligibility from database records.
    Returns structured requirements with met/unmet status for every requirement.
    """
    req = CERT_REQUIREMENTS.get(path_id)
    if not req:
        return {"eligible": False, "reason": "Unknown path", "requirements": {}}

    # ── 1. Lesson completion ──────────────────────────────────────────────────
    lp_result = await session.exec(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.path_id == path_id,
            LessonProgress.completed == True,
        )
    )
    completed_lesson_ids = {r.lesson_id for r in lp_result.all()}

    # Only count content lessons (not quiz lessons) toward the lesson requirement
    content_lesson_ids = set(req["lesson_ids"])
    completed_content_lessons = len(completed_lesson_ids & content_lesson_ids)
    required_lessons = req["required_lessons"]
    lessons_met = completed_content_lessons >= required_lessons

    # ── 2. Codercise pass rate ────────────────────────────────────────────────
    cs_result = await session.exec(
        select(CodeSubmission).where(CodeSubmission.user_id == user_id)
    )
    all_subs = cs_result.all()

    required_codercise_ids = set(req["codercise_ids"])
    passed_codercise_ids = {
        s.codercise_id
        for s in all_subs
        if s.passed and s.codercise_id in required_codercise_ids
    }
    codercises_passed = len(passed_codercise_ids)
    required_codercises = req["required_codercises"]
    codercises_met = codercises_passed >= required_codercises

    # ── 3. Module quiz performance ────────────────────────────────────────────
    qs_result = await session.exec(
        select(QuizSubmission).where(
            QuizSubmission.user_id == user_id,
            QuizSubmission.path_id == path_id,
        )
    )
    quiz_rows = qs_result.all()

    # Best score per quiz_id
    best_quiz_scores: dict[str, int] = {}
    for row in quiz_rows:
        existing = best_quiz_scores.get(row.quiz_id, -1)
        if row.score > existing:
            best_quiz_scores[row.quiz_id] = row.score

    passing_score = req["passing_quiz_score"]
    required_quiz_ids = set(req["quiz_ids"])
    passed_quiz_ids = {
        qid
        for qid, score in best_quiz_scores.items()
        if score >= passing_score and qid in required_quiz_ids
    }
    quizzes_passed = len(passed_quiz_ids)
    required_quizzes = req["required_quizzes"]
    quizzes_met = quizzes_passed >= required_quizzes

    # Per-quiz breakdown for the frontend
    quiz_details = []
    for qid in sorted(required_quiz_ids):
        best = best_quiz_scores.get(qid)
        quiz_details.append({
            "quiz_id":       qid,
            "best_score":    best,
            "passing_score": passing_score,
            "attempted":     best is not None,
            "passed":        best is not None and best >= passing_score,
        })

    # ── Overall eligibility ───────────────────────────────────────────────────
    eligible = lessons_met and codercises_met and quizzes_met

    return {
        "eligible":   eligible,
        "path_id":    path_id,
        "path_title": req["path_title"],
        "requirements": {
            "lessons": {
                "label":      "Complete all content lessons",
                "required":   required_lessons,
                "completed":  completed_content_lessons,
                "met":        lessons_met,
                "evidence":   f"{completed_content_lessons} of {required_lessons} lessons completed",
            },
            "codercises": {
                "label":      "Pass all coding exercises",
                "required":   required_codercises,
                "passed":     codercises_passed,
                "met":        codercises_met,
                "evidence":   f"{codercises_passed} of {required_codercises} codercises passed",
            },
            "quizzes": {
                "label":      f"Pass at least {required_quizzes} module quiz(zes) with ≥{passing_score}%",
                "required":   required_quizzes,
                "passed":     quizzes_passed,
                "total":      len(required_quiz_ids),
                "met":        quizzes_met,
                "passing_score": passing_score,
                "evidence":   f"{quizzes_passed} of {required_quizzes} required quizzes passed",
                "details":    quiz_details,
            },
        },
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/eligibility/{path_id}")
async def check_eligibility(
    path_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return structured eligibility data including per-requirement progress."""
    return await _check_eligibility(current_user.id, path_id, session)


class IssueRequest(BaseModel):
    path_id: str
    final_score: int = 0


@router.post("/issue")
async def issue_certificate(
    data: IssueRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Issue a certificate if eligible. Idempotent — returns existing cert if already issued.
    Eligibility is verified server-side; client claims are never trusted.
    """
    # Return existing certificate
    existing = await session.exec(
        select(Certificate).where(
            Certificate.user_id == current_user.id,
            Certificate.path_id == data.path_id,
        )
    )
    cert = existing.first()
    if cert:
        return CertificateRead.model_validate(cert).model_dump()

    # Verify eligibility from DB
    elig = await _check_eligibility(current_user.id, data.path_id, session)
    if not elig["eligible"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Certification requirements not met",
                "requirements": elig["requirements"],
            },
        )

    req = elig["requirements"]
    cert = Certificate(
        cert_id=_generate_cert_id(data.path_id, current_user.id),
        user_id=current_user.id,
        path_id=data.path_id,
        path_title=elig["path_title"],
        lessons_completed=req["lessons"]["completed"],
        codercises_passed=req["codercises"]["passed"],
        final_score=data.final_score,
    )
    session.add(cert)
    await session.commit()
    await session.refresh(cert)
    return CertificateRead.model_validate(cert).model_dump()


@router.get("/me")
async def my_certificates(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(
        select(Certificate).where(Certificate.user_id == current_user.id)
    )
    return [CertificateRead.model_validate(r).model_dump() for r in result.all()]


@router.get("/{cert_id}")
async def verify_certificate(
    cert_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Public certificate verification — no authentication required.
    Works from any browser, independent of localStorage.
    Returns 404 for unknown cert IDs.
    """
    result = await session.exec(
        select(Certificate).where(Certificate.cert_id == cert_id)
    )
    cert = result.first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    from app.models.user import User as UserModel
    user_result = await session.exec(
        select(UserModel).where(UserModel.id == cert.user_id)
    )
    user = user_result.first()

    data = CertificateRead.model_validate(cert).model_dump()
    data["learner_name"] = user.username if user else "Unknown"
    return data

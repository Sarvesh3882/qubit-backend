"""
Placement assessment API.

POST /assessment/submit   — save (or overwrite) a user's placement result
GET  /assessment/me       — retrieve the stored result for the current user
DELETE /assessment/me     — clear the result so the user can retake
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.adaptive import (
    PlacementAssessment,
    PlacementAssessmentCreate,
    PlacementAssessmentRead,
)

router = APIRouter(prefix="/assessment", tags=["assessment"])


def _to_read(row: PlacementAssessment) -> dict:
    return PlacementAssessmentRead(
        id=row.id,
        user_id=row.user_id,
        score=row.score,
        level=row.level,
        suggested_difficulty=row.suggested_difficulty,
        recommended_path_id=row.recommended_path_id,
        recommended_module_id=row.recommended_module_id,
        strong_concepts=json.loads(row.strong_concepts),
        weak_concepts=json.loads(row.weak_concepts),
        per_concept_scores=json.loads(row.per_concept_scores),
        total_questions=row.total_questions,
        correct_answers=row.correct_answers,
        completed_at=row.completed_at,
        skipped=row.skipped,
    ).model_dump()


@router.post("/submit")
async def submit_assessment(
    data: PlacementAssessmentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upsert the placement assessment result for the current user."""
    result = await session.exec(
        select(PlacementAssessment).where(
            PlacementAssessment.user_id == current_user.id
        )
    )
    row = result.first()

    serialised = {
        "score": data.score,
        "level": data.level,
        "suggested_difficulty": data.suggested_difficulty,
        "recommended_path_id": data.recommended_path_id,
        "recommended_module_id": data.recommended_module_id,
        "strong_concepts": json.dumps(data.strong_concepts),
        "weak_concepts": json.dumps(data.weak_concepts),
        "per_concept_scores": json.dumps(data.per_concept_scores),
        "total_questions": data.total_questions,
        "correct_answers": data.correct_answers,
        "skipped": data.skipped,
        "completed_at": datetime.now(timezone.utc),
    }

    if row:
        for k, v in serialised.items():
            setattr(row, k, v)
    else:
        row = PlacementAssessment(user_id=current_user.id, **serialised)
        session.add(row)

    await session.commit()
    await session.refresh(row)
    return _to_read(row)


@router.get("/me")
async def get_my_assessment(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the stored assessment result, or null if never taken."""
    result = await session.exec(
        select(PlacementAssessment).where(
            PlacementAssessment.user_id == current_user.id
        )
    )
    row = result.first()
    if not row:
        return None
    return _to_read(row)


@router.delete("/me")
async def retake_assessment(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete the stored result so the learner can start fresh."""
    result = await session.exec(
        select(PlacementAssessment).where(
            PlacementAssessment.user_id == current_user.id
        )
    )
    row = result.first()
    if row:
        await session.delete(row)
        await session.commit()
    return {"status": "ok"}

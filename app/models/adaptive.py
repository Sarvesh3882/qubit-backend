"""
Adaptive learning models for QUBIT.

Design principles:
- PlacementAssessment: one row per user, upserted on retake.
- Certificate: one row per (user_id, path_id) — unique constraint prevents duplicates.
- We do NOT store a separate ConceptMastery or ModuleMastery table.
  Those values are DERIVED at query time from the existing LessonProgress
  and CodeSubmission tables to avoid data duplication.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, JSON, Column
from sqlalchemy import UniqueConstraint
import json


# ── Placement Assessment ───────────────────────────────────────────────────────
# One row per user.  Re-taking the assessment updates the same row.

class PlacementAssessment(SQLModel, table=True):
    __tablename__ = "placement_assessments"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, unique=True)

    # Scalar results
    score: int                          # 0–100
    level: str                          # "beginner" | "intermediate" | "advanced"
    suggested_difficulty: str           # "normal" | "accelerated" | "review"

    # Recommended starting point
    recommended_path_id: str
    recommended_module_id: str

    # JSON-serialised lists / dicts stored as TEXT (SQLite) or JSONB (Postgres)
    strong_concepts: str = Field(default="[]")   # JSON array of concept keys
    weak_concepts:   str = Field(default="[]")   # JSON array of concept keys
    per_concept_scores: str = Field(default="{}")# JSON object {concept: score}

    # Metadata
    total_questions:  int = 0
    correct_answers:  int = 0
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    skipped: bool = False


class PlacementAssessmentCreate(SQLModel):
    score: int
    level: str
    suggested_difficulty: str
    recommended_path_id: str
    recommended_module_id: str
    strong_concepts: List[str] = []
    weak_concepts: List[str] = []
    per_concept_scores: dict = {}
    total_questions: int = 0
    correct_answers: int = 0
    skipped: bool = False


class PlacementAssessmentRead(SQLModel):
    id: int
    user_id: int
    score: int
    level: str
    suggested_difficulty: str
    recommended_path_id: str
    recommended_module_id: str
    strong_concepts: List[str]
    weak_concepts: List[str]
    per_concept_scores: dict
    total_questions: int
    correct_answers: int
    completed_at: datetime
    skipped: bool


# ── Certificate ────────────────────────────────────────────────────────────────
# One row per (user, path).  Unique constraint prevents duplicate issuance.
# blockchain_* fields are nullable — populated only when real chain integration exists.

class Certificate(SQLModel, table=True):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("user_id", "path_id", name="uq_cert_user_path"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cert_id: str = Field(index=True, unique=True)   # e.g. "QUBIT-FQC-20260924-A3F7"
    user_id: int = Field(foreign_key="users.id", index=True)

    path_id: str
    path_title: str

    # Learning record at time of issue
    lessons_completed: int = 0
    codercises_passed: int = 0
    final_score: int = 0          # 0 if not applicable

    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Blockchain — intentionally nullable.  Do NOT populate with fake data.
    blockchain_network:      Optional[str] = None
    blockchain_tx_hash:      Optional[str] = None
    blockchain_contract:     Optional[str] = None
    blockchain_token_id:     Optional[str] = None
    blockchain_verify_url:   Optional[str] = None


class CertificateRead(SQLModel):
    id: int
    cert_id: str
    user_id: int
    path_id: str
    path_title: str
    lessons_completed: int
    codercises_passed: int
    final_score: int
    issued_at: datetime
    blockchain_network:    Optional[str]
    blockchain_tx_hash:    Optional[str]
    blockchain_contract:   Optional[str]
    blockchain_token_id:   Optional[str]
    blockchain_verify_url: Optional[str]

"""
Classroom models for QUBIT.

Three tables:
  Classroom        — one per teacher-created class (name, invite code, owner)
  ClassMembership  — many-to-many users ↔ classrooms (students who joined)
  ClassAssignment  — content assigned to a classroom by the teacher

Design principles:
  - We do NOT duplicate LessonProgress, CodeSubmission, QuizSubmission, or
    Certificate data. Analytics are derived at query time from those tables.
  - ClassAssignment references content by (content_type, content_id) strings
    that match IDs in curriculum_meta.py. No FK to a curriculum table — the
    curriculum is static code, not a DB table.
  - Invite codes are short alphanumeric strings (e.g. "QUBIT-7K42") generated
    once at creation and never rotated. Uniqueness is enforced by the DB.
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


# ── Classroom ──────────────────────────────────────────────────────────────────

class Classroom(SQLModel, table=True):
    __tablename__ = "classrooms"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Owner — must be an instructor (is_instructor=True)
    instructor_id: int = Field(foreign_key="users.id", index=True)

    name: str = Field(index=True)
    description: Optional[str] = None

    # Short unique join code, e.g. "QUBIT-7K42"
    invite_code: str = Field(unique=True, index=True)

    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClassroomCreate(SQLModel):
    name: str
    description: Optional[str] = None


class ClassroomRead(SQLModel):
    id: int
    instructor_id: int
    name: str
    description: Optional[str]
    invite_code: str
    is_active: bool
    created_at: datetime
    # Populated by the API layer, not a DB column
    student_count: int = 0
    assignment_count: int = 0


# ── ClassMembership ────────────────────────────────────────────────────────────

class ClassMembership(SQLModel, table=True):
    """A student joining a classroom.  One row per (student, classroom) pair."""
    __tablename__ = "class_memberships"
    __table_args__ = (
        UniqueConstraint("student_id", "classroom_id", name="uq_membership"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    classroom_id: int = Field(foreign_key="classrooms.id", index=True)
    student_id: int = Field(foreign_key="users.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClassMembershipRead(SQLModel):
    id: int
    classroom_id: int
    student_id: int
    joined_at: datetime
    # Populated by the API layer
    username: str = ""
    full_name: Optional[str] = None
    email: str = ""


# ── ClassAssignment ────────────────────────────────────────────────────────────

CONTENT_TYPES = frozenset({"module", "lesson", "quiz", "codercise"})

class ClassAssignment(SQLModel, table=True):
    """
    A piece of QUBIT content assigned to a classroom.

    content_type: "module" | "lesson" | "quiz" | "codercise"
    content_id:   the ID string from curriculum_meta, e.g. "iqc", "iqc-1", "iqc-quiz", "iqc-1-c1"

    Uniqueness: (classroom_id, content_type, content_id) — prevents duplicate assignments.
    """
    __tablename__ = "class_assignments"
    __table_args__ = (
        UniqueConstraint("classroom_id", "content_type", "content_id", name="uq_assignment"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    classroom_id: int = Field(foreign_key="classrooms.id", index=True)

    content_type: str   # "module" | "lesson" | "quiz" | "codercise"
    content_id: str     # e.g. "iqc", "iqc-1", "iqc-quiz", "iqc-1-c1"
    title: str          # human-readable label (denormalised for display speed)

    due_date: Optional[datetime] = None
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClassAssignmentCreate(SQLModel):
    content_type: str
    content_id: str
    title: str
    due_date: Optional[datetime] = None


class ClassAssignmentRead(SQLModel):
    id: int
    classroom_id: int
    content_type: str
    content_id: str
    title: str
    due_date: Optional[datetime]
    assigned_at: datetime

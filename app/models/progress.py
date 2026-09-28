from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class LessonProgress(SQLModel, table=True):
    __tablename__ = "lesson_progress"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    lesson_id: str = Field(index=True)
    module_id: str
    path_id: str
    completed: bool = False
    score: Optional[float] = None
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class CodeSubmission(SQLModel, table=True):
    __tablename__ = "code_submissions"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    codercise_id: str = Field(index=True)
    lesson_id: str
    code: str
    passed: bool = False
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuizSubmission(SQLModel, table=True):
    """One row per quiz attempt. Multiple attempts are allowed; only the best score counts."""
    __tablename__ = "quiz_submissions"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    quiz_id: str = Field(index=True)          # e.g. "iqc-quiz"
    module_id: str                             # e.g. "iqc"
    path_id: str                               # e.g. "fqc"
    score: int                                 # 0–100
    correct: int                               # number of correct answers
    total: int                                 # total questions
    passed: bool = False                       # score >= passing threshold
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LessonProgressCreate(SQLModel):
    lesson_id: str
    module_id: str
    path_id: str
    completed: bool = False
    score: Optional[float] = None


class LessonProgressRead(SQLModel):
    id: int
    user_id: int
    lesson_id: str
    module_id: str
    path_id: str
    completed: bool
    score: Optional[float]
    last_accessed: datetime
    completed_at: Optional[datetime]

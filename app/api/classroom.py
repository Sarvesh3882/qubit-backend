"""
Classroom API — QUBIT Classroom feature.

Teacher endpoints (require is_instructor=True):
  POST   /classroom/                          create classroom
  GET    /classroom/mine                      list my classrooms (as teacher)
  GET    /classroom/{id}                      classroom detail
  DELETE /classroom/{id}                      deactivate classroom
  GET    /classroom/{id}/students             enrolled students
  POST   /classroom/{id}/assignments          add assignment
  DELETE /classroom/{id}/assignments/{aid}    remove assignment
  GET    /classroom/{id}/analytics            class-wide progress analytics

Student endpoints (any authenticated user):
  POST   /classroom/join                      join by invite code
  GET    /classroom/enrolled                  list classrooms I joined
  GET    /classroom/{id}/assignments          my assignments + my completion status

Analytics pull from LessonProgress, CodeSubmission, QuizSubmission — never duplicated.
"""
from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.classroom import (
    Classroom, ClassroomCreate, ClassroomRead,
    ClassMembership, ClassMembershipRead,
    ClassAssignment, ClassAssignmentCreate, ClassAssignmentRead,
    CONTENT_TYPES,
)
from app.models.progress import LessonProgress, CodeSubmission, QuizSubmission
from app.services.curriculum_meta import MODULE_META, MODULE_ORDER

router = APIRouter(prefix="/classroom", tags=["classroom"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _require_instructor(user: User) -> None:
    if not user.is_instructor:
        raise HTTPException(status_code=403, detail="Instructor account required")


def _require_classroom_owner(classroom: Classroom, user: User) -> None:
    if classroom.instructor_id != user.id:
        raise HTTPException(status_code=403, detail="Not your classroom")


async def _get_classroom_or_404(
    classroom_id: int, session: AsyncSession
) -> Classroom:
    result = await session.exec(
        select(Classroom).where(Classroom.id == classroom_id)
    )
    classroom = result.first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom


def _make_invite_code() -> str:
    """Generate a short unique code like QUBIT-7K42."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=4))
    return f"QUBIT-{suffix}"


async def _unique_invite_code(session: AsyncSession) -> str:
    """Generate an invite code guaranteed not to already exist in the DB."""
    for _ in range(10):
        code = _make_invite_code()
        existing = await session.exec(
            select(Classroom).where(Classroom.invite_code == code)
        )
        if not existing.first():
            return code
    raise HTTPException(status_code=500, detail="Could not generate unique invite code")


async def _classroom_counts(
    classroom_id: int, session: AsyncSession
) -> tuple[int, int]:
    """Return (student_count, assignment_count) for a classroom."""
    members = await session.exec(
        select(ClassMembership).where(ClassMembership.classroom_id == classroom_id)
    )
    assignments = await session.exec(
        select(ClassAssignment).where(ClassAssignment.classroom_id == classroom_id)
    )
    return len(members.all()), len(assignments.all())


def _enrich_classroom(c: Classroom, student_count: int, assignment_count: int) -> dict:
    return ClassroomRead(
        id=c.id,
        instructor_id=c.instructor_id,
        name=c.name,
        description=c.description,
        invite_code=c.invite_code,
        is_active=c.is_active,
        created_at=c.created_at,
        student_count=student_count,
        assignment_count=assignment_count,
    ).model_dump()


# ── Teacher: classroom CRUD ────────────────────────────────────────────────────

@router.post("/", response_model=dict, status_code=201)
async def create_classroom(
    data: ClassroomCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new classroom. Requires is_instructor=True."""
    _require_instructor(current_user)
    invite_code = await _unique_invite_code(session)
    classroom = Classroom(
        instructor_id=current_user.id,
        name=data.name,
        description=data.description,
        invite_code=invite_code,
    )
    session.add(classroom)
    await session.commit()
    await session.refresh(classroom)
    return _enrich_classroom(classroom, 0, 0)


@router.get("/mine", response_model=list)
async def my_classrooms(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all classrooms owned by the current instructor."""
    _require_instructor(current_user)
    result = await session.exec(
        select(Classroom).where(
            Classroom.instructor_id == current_user.id,
            Classroom.is_active == True,
        ).order_by(Classroom.created_at.desc())  # type: ignore[arg-type]
    )
    classrooms = result.all()
    out = []
    for c in classrooms:
        sc, ac = await _classroom_counts(c.id, session)
        out.append(_enrich_classroom(c, sc, ac))
    return out


# ── Student: join + enrolled  (MUST be before /{classroom_id} to avoid swallowing) ──

@router.post("/join", response_model=dict, status_code=201)
async def join_classroom(
    payload: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Join a classroom using an invite code.
    Body: { "invite_code": "QUBIT-7K42" }
    Any authenticated user (including instructors) can join as a student.
    """
    invite_code = (payload.get("invite_code") or "").strip().upper()
    if not invite_code:
        raise HTTPException(status_code=400, detail="invite_code is required")

    result = await session.exec(
        select(Classroom).where(
            Classroom.invite_code == invite_code,
            Classroom.is_active == True,
        )
    )
    classroom = result.first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found — check the invite code")

    if classroom.instructor_id == current_user.id:
        raise HTTPException(status_code=400, detail="You are the instructor of this classroom")

    existing = await session.exec(
        select(ClassMembership).where(
            ClassMembership.classroom_id == classroom.id,
            ClassMembership.student_id == current_user.id,
        )
    )
    if existing.first():
        sc, ac = await _classroom_counts(classroom.id, session)
        return _enrich_classroom(classroom, sc, ac)

    membership = ClassMembership(
        classroom_id=classroom.id,
        student_id=current_user.id,
    )
    session.add(membership)
    await session.commit()

    sc, ac = await _classroom_counts(classroom.id, session)
    return _enrich_classroom(classroom, sc, ac)


@router.get("/enrolled", response_model=list)
async def enrolled_classrooms(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all classrooms the current user has joined as a student."""
    mem_result = await session.exec(
        select(ClassMembership).where(ClassMembership.student_id == current_user.id)
    )
    memberships = mem_result.all()

    out = []
    for m in memberships:
        c_result = await session.exec(
            select(Classroom).where(
                Classroom.id == m.classroom_id,
                Classroom.is_active == True,
            )
        )
        classroom = c_result.first()
        if not classroom:
            continue

        instr = await session.exec(select(User).where(User.id == classroom.instructor_id))
        instructor = instr.first()

        sc, ac = await _classroom_counts(classroom.id, session)
        data = _enrich_classroom(classroom, sc, ac)
        data["instructor_name"] = instructor.username if instructor else "Unknown"
        data["joined_at"] = m.joined_at.isoformat()
        out.append(data)

    return out


@router.get("/{classroom_id}", response_model=dict)
async def get_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get classroom detail.  Accessible by:
      - The owning instructor
      - Any enrolled student
    """
    classroom = await _get_classroom_or_404(classroom_id, session)

    # Check access: owner or enrolled student
    if classroom.instructor_id != current_user.id:
        mem = await session.exec(
            select(ClassMembership).where(
                ClassMembership.classroom_id == classroom_id,
                ClassMembership.student_id == current_user.id,
            )
        )
        if not mem.first():
            raise HTTPException(status_code=403, detail="Not a member of this classroom")

    sc, ac = await _classroom_counts(classroom_id, session)
    return _enrich_classroom(classroom, sc, ac)


@router.delete("/{classroom_id}", status_code=204)
async def deactivate_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Soft-delete (deactivate) a classroom."""
    _require_instructor(current_user)
    classroom = await _get_classroom_or_404(classroom_id, session)
    _require_classroom_owner(classroom, current_user)
    classroom.is_active = False
    await session.commit()


# ── Teacher: student management ────────────────────────────────────────────────

@router.get("/{classroom_id}/students", response_model=list)
async def list_students(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all enrolled students with progress summary."""
    _require_instructor(current_user)
    classroom = await _get_classroom_or_404(classroom_id, session)
    _require_classroom_owner(classroom, current_user)

    mem_result = await session.exec(
        select(ClassMembership).where(ClassMembership.classroom_id == classroom_id)
    )
    memberships = mem_result.all()

    # Fetch user objects for all members
    student_ids = [m.student_id for m in memberships]
    students: dict[int, User] = {}
    for sid in student_ids:
        u = await session.exec(select(User).where(User.id == sid))
        user = u.first()
        if user:
            students[sid] = user

    # Per-student progress snapshot
    out = []
    for m in memberships:
        user = students.get(m.student_id)
        if not user:
            continue

        # Lessons completed
        lp = await session.exec(
            select(LessonProgress).where(
                LessonProgress.user_id == m.student_id,
                LessonProgress.completed == True,
            )
        )
        completed_lessons = len(lp.all())

        # Codercises passed
        cs = await session.exec(
            select(CodeSubmission).where(
                CodeSubmission.user_id == m.student_id,
                CodeSubmission.passed == True,
            )
        )
        # Unique codercises passed
        passed_codercises = len({r.codercise_id for r in cs.all()})

        # Best quiz scores
        qs = await session.exec(
            select(QuizSubmission).where(QuizSubmission.user_id == m.student_id)
        )
        quiz_rows = qs.all()
        best_quiz: dict[str, int] = {}
        for row in quiz_rows:
            if row.score > best_quiz.get(row.quiz_id, -1):
                best_quiz[row.quiz_id] = row.score
        avg_quiz = int(sum(best_quiz.values()) / len(best_quiz)) if best_quiz else 0

        out.append({
            "student_id":         m.student_id,
            "username":           user.username,
            "full_name":          user.full_name,
            "email":              user.email,
            "joined_at":          m.joined_at.isoformat(),
            "completed_lessons":  completed_lessons,
            "passed_codercises":  passed_codercises,
            "avg_quiz_score":     avg_quiz,
            "quizzes_attempted":  len(best_quiz),
        })

    return out


# ── Teacher: assignments ────────────────────────────────────────────────────────

@router.post("/{classroom_id}/assignments", response_model=dict, status_code=201)
async def add_assignment(
    classroom_id: int,
    data: ClassAssignmentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Assign content to a classroom. content_type: module|lesson|quiz|codercise"""
    _require_instructor(current_user)
    classroom = await _get_classroom_or_404(classroom_id, session)
    _require_classroom_owner(classroom, current_user)

    if data.content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"content_type must be one of: {', '.join(sorted(CONTENT_TYPES))}",
        )

    # Prevent duplicate assignment
    existing = await session.exec(
        select(ClassAssignment).where(
            ClassAssignment.classroom_id == classroom_id,
            ClassAssignment.content_type == data.content_type,
            ClassAssignment.content_id == data.content_id,
        )
    )
    if existing.first():
        raise HTTPException(status_code=409, detail="This content is already assigned")

    assignment = ClassAssignment(
        classroom_id=classroom_id,
        content_type=data.content_type,
        content_id=data.content_id,
        title=data.title,
        due_date=data.due_date,
    )
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return ClassAssignmentRead.model_validate(assignment).model_dump()


@router.delete("/{classroom_id}/assignments/{assignment_id}", status_code=204)
async def remove_assignment(
    classroom_id: int,
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove an assignment from a classroom."""
    _require_instructor(current_user)
    classroom = await _get_classroom_or_404(classroom_id, session)
    _require_classroom_owner(classroom, current_user)

    result = await session.exec(
        select(ClassAssignment).where(
            ClassAssignment.id == assignment_id,
            ClassAssignment.classroom_id == classroom_id,
        )
    )
    assignment = result.first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await session.delete(assignment)
    await session.commit()


# ── Teacher: analytics ─────────────────────────────────────────────────────────

@router.get("/{classroom_id}/analytics", response_model=dict)
async def class_analytics(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Class-wide analytics derived from existing progress tables.
    Returns:
      - summary counts (total_students, active_students, etc.)
      - per-module mastery across the class
      - quiz performance per module quiz
      - codercise pass rates per module
      - assignment completion rates
      - students needing attention (low progress)
    """
    _require_instructor(current_user)
    classroom = await _get_classroom_or_404(classroom_id, session)
    _require_classroom_owner(classroom, current_user)

    # Enrolled students
    mem_result = await session.exec(
        select(ClassMembership).where(ClassMembership.classroom_id == classroom_id)
    )
    memberships = mem_result.all()
    student_ids = [m.student_id for m in memberships]
    total_students = len(student_ids)

    if total_students == 0:
        return {
            "classroom_id": classroom_id,
            "total_students": 0,
            "active_students": 0,
            "module_mastery": [],
            "quiz_performance": [],
            "codercise_performance": [],
            "assignment_completion": [],
            "needs_attention": [],
        }

    # ── Collect all progress rows for all students ────────────────────────────

    all_lp: list[LessonProgress] = []
    all_cs: list[CodeSubmission] = []
    all_qs: list[QuizSubmission] = []

    for sid in student_ids:
        lp = await session.exec(
            select(LessonProgress).where(
                LessonProgress.user_id == sid,
                LessonProgress.completed == True,
            )
        )
        all_lp.extend(lp.all())

        cs = await session.exec(
            select(CodeSubmission).where(CodeSubmission.user_id == sid)
        )
        all_cs.extend(cs.all())

        qs = await session.exec(
            select(QuizSubmission).where(QuizSubmission.user_id == sid)
        )
        all_qs.extend(qs.all())

    # ── Active students: completed at least 1 lesson ──────────────────────────
    active_student_ids = {lp.user_id for lp in all_lp}
    active_students = len(active_student_ids & set(student_ids))

    # ── Module mastery (% of class who completed all lessons in module) ───────
    module_mastery = []
    for mid in MODULE_ORDER:
        mod = MODULE_META.get(mid, {})
        lesson_ids = set(mod.get("lesson_ids", []))
        if not lesson_ids:
            continue
        # For each student count if they completed all lessons in this module
        mastered = 0
        for sid in student_ids:
            student_completed = {
                r.lesson_id for r in all_lp
                if r.user_id == sid and r.lesson_id in lesson_ids
            }
            if lesson_ids.issubset(student_completed):
                mastered += 1
        pct = int(mastered / total_students * 100) if total_students else 0
        module_mastery.append({
            "module_id":    mid,
            "title":        mod.get("title", mid),
            "mastery_pct":  pct,
            "mastered":     mastered,
            "total":        total_students,
        })

    # ── Quiz performance per quiz ─────────────────────────────────────────────
    quiz_ids = [MODULE_META[mid]["quiz_id"] for mid in MODULE_ORDER if mid in MODULE_META]
    quiz_performance = []
    for qid in quiz_ids:
        # Best score per student for this quiz
        quiz_rows = [r for r in all_qs if r.quiz_id == qid]
        best_per_student: dict[int, int] = {}
        for row in quiz_rows:
            if row.score > best_per_student.get(row.user_id, -1):
                best_per_student[row.user_id] = row.score
        attempted = len(best_per_student)
        avg_score = int(sum(best_per_student.values()) / attempted) if attempted else 0
        passed = sum(1 for s in best_per_student.values() if s >= 70)
        # Find module title for quiz
        module_title = next(
            (MODULE_META[mid]["title"] for mid in MODULE_ORDER
             if MODULE_META.get(mid, {}).get("quiz_id") == qid),
            qid
        )
        quiz_performance.append({
            "quiz_id":      qid,
            "module_title": module_title,
            "attempted":    attempted,
            "avg_score":    avg_score,
            "passed":       passed,
            "total":        total_students,
        })

    # ── Codercise pass rates per module ───────────────────────────────────────
    codercise_performance = []
    for mid in MODULE_ORDER:
        mod = MODULE_META.get(mid, {})
        codercise_ids = set(mod.get("codercise_ids", []))
        if not codercise_ids:
            continue
        # Unique (student, codercise) passes
        passes: dict[int, set[str]] = {sid: set() for sid in student_ids}
        for row in all_cs:
            if row.passed and row.codercise_id in codercise_ids and row.user_id in passes:
                passes[row.user_id].add(row.codercise_id)
        # Students who passed all codercises in this module
        all_passed = sum(1 for sid in student_ids if codercise_ids.issubset(passes[sid]))
        avg_passed = sum(len(v) for v in passes.values()) / total_students if total_students else 0
        pct = int(all_passed / total_students * 100) if total_students else 0
        codercise_performance.append({
            "module_id":      mid,
            "title":          mod.get("title", mid),
            "completion_pct": pct,
            "avg_passed":     round(avg_passed, 1),
            "total_in_module": len(codercise_ids),
            "total_students": total_students,
        })

    # ── Assignment completion ─────────────────────────────────────────────────
    assignments_result = await session.exec(
        select(ClassAssignment).where(ClassAssignment.classroom_id == classroom_id)
    )
    assignments = assignments_result.all()

    assignment_completion = []
    for a in assignments:
        completed = 0
        if a.content_type == "lesson":
            cids = {r.lesson_id for r in all_lp if r.lesson_id == a.content_id}
            # Count unique students who completed this lesson
            completed = len({r.user_id for r in all_lp if r.lesson_id == a.content_id})
        elif a.content_type == "module":
            mod = MODULE_META.get(a.content_id, {})
            lids = set(mod.get("lesson_ids", []))
            completed = sum(
                1 for sid in student_ids
                if lids and lids.issubset({r.lesson_id for r in all_lp if r.user_id == sid})
            )
        elif a.content_type == "quiz":
            completed = len({r.user_id for r in all_qs if r.quiz_id == a.content_id})
        elif a.content_type == "codercise":
            completed = len({r.user_id for r in all_cs if r.codercise_id == a.content_id and r.passed})

        pct = int(completed / total_students * 100) if total_students else 0
        assignment_completion.append({
            "assignment_id":   a.id,
            "content_type":    a.content_type,
            "content_id":      a.content_id,
            "title":           a.title,
            "due_date":        a.due_date.isoformat() if a.due_date else None,
            "completed":       completed,
            "total":           total_students,
            "completion_pct":  pct,
        })

    # ── Students needing attention: < 50% of assigned lessons completed ───────
    total_assigned_lessons = sum(
        len(MODULE_META.get(a.content_id, {}).get("lesson_ids", []))
        if a.content_type == "module"
        else (1 if a.content_type == "lesson" else 0)
        for a in assignments
    )

    needs_attention = []
    if total_assigned_lessons > 0:
        for sid in student_ids:
            student_completed = {r.lesson_id for r in all_lp if r.user_id == sid}
            assigned_lesson_ids: set[str] = set()
            for a in assignments:
                if a.content_type == "module":
                    assigned_lesson_ids.update(
                        MODULE_META.get(a.content_id, {}).get("lesson_ids", [])
                    )
                elif a.content_type == "lesson":
                    assigned_lesson_ids.add(a.content_id)

            if not assigned_lesson_ids:
                continue
            done = len(student_completed & assigned_lesson_ids)
            pct = int(done / len(assigned_lesson_ids) * 100)
            if pct < 50:
                user_r = await session.exec(select(User).where(User.id == sid))
                user = user_r.first()
                needs_attention.append({
                    "student_id":      sid,
                    "username":        user.username if user else str(sid),
                    "completion_pct":  pct,
                    "completed":       done,
                    "total_assigned":  len(assigned_lesson_ids),
                })
        needs_attention.sort(key=lambda x: x["completion_pct"])

    return {
        "classroom_id":           classroom_id,
        "total_students":         total_students,
        "active_students":        active_students,
        "module_mastery":         module_mastery,
        "quiz_performance":       quiz_performance,
        "codercise_performance":  codercise_performance,
        "assignment_completion":  assignment_completion,
        "needs_attention":        needs_attention,
    }


# ── Student: view assignments ──────────────────────────────────────────────────

@router.get("/{classroom_id}/assignments", response_model=list)
async def get_assignments(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all assignments for a classroom.
    For students: includes their own completion status.
    For teachers: includes class-wide completion count.
    Accessible by owner and enrolled students.
    """
    classroom = await _get_classroom_or_404(classroom_id, session)

    is_owner = classroom.instructor_id == current_user.id
    if not is_owner:
        # Verify student membership
        mem = await session.exec(
            select(ClassMembership).where(
                ClassMembership.classroom_id == classroom_id,
                ClassMembership.student_id == current_user.id,
            )
        )
        if not mem.first():
            raise HTTPException(status_code=403, detail="Not a member of this classroom")

    result = await session.exec(
        select(ClassAssignment).where(ClassAssignment.classroom_id == classroom_id)
    )
    assignments = result.all()

    # Per-student completion for non-teacher view
    if not is_owner:
        lp_result = await session.exec(
            select(LessonProgress).where(
                LessonProgress.user_id == current_user.id,
                LessonProgress.completed == True,
            )
        )
        completed_lessons = {r.lesson_id for r in lp_result.all()}

        cs_result = await session.exec(
            select(CodeSubmission).where(
                CodeSubmission.user_id == current_user.id,
                CodeSubmission.passed == True,
            )
        )
        passed_codercises = {r.codercise_id for r in cs_result.all()}

        qs_result = await session.exec(
            select(QuizSubmission).where(
                QuizSubmission.user_id == current_user.id,
            )
        )
        quiz_rows = qs_result.all()
        best_quiz: dict[str, int] = {}
        for row in quiz_rows:
            if row.score > best_quiz.get(row.quiz_id, -1):
                best_quiz[row.quiz_id] = row.score

    out = []
    for a in assignments:
        row: dict = ClassAssignmentRead.model_validate(a).model_dump()

        if not is_owner:
            # Determine individual completion
            if a.content_type == "lesson":
                row["completed"] = a.content_id in completed_lessons
                row["status"] = "done" if row["completed"] else "pending"
            elif a.content_type == "module":
                mod = MODULE_META.get(a.content_id, {})
                lids = set(mod.get("lesson_ids", []))
                done = len(lids & completed_lessons) if lids else 0
                row["completed"] = lids.issubset(completed_lessons) if lids else False
                row["lessons_done"] = done
                row["lessons_total"] = len(lids)
                row["status"] = "done" if row["completed"] else ("in_progress" if done > 0 else "pending")
            elif a.content_type == "quiz":
                best = best_quiz.get(a.content_id)
                row["completed"] = best is not None
                row["best_score"] = best
                row["status"] = "done" if best is not None else "pending"
            elif a.content_type == "codercise":
                row["completed"] = a.content_id in passed_codercises
                row["status"] = "done" if row["completed"] else "pending"

        out.append(row)

    return out

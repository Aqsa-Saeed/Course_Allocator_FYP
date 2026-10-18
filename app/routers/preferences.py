"""
Coordinator side of preferences: review what faculty requested and approve or
reject it. Each decision is written to the audit log in the same transaction.
Only Department Coordinators can decide; Program Coordinators can read.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, commit_or_409, get_scope, require_writer, scoped_preferences,
)
from app.database import get_db
from app.models import InstructorPreference, Semester
from app.schemas.preferences import PreferenceAdminOut
from app.services.audit import log_action

router = APIRouter(prefix="/preferences", tags=["preferences"])


def admin_out(p: InstructorPreference) -> PreferenceAdminOut:
    return PreferenceAdminOut(
        id=p.id, course_id=p.course_id, course_code=p.course.code, course_title=p.course.title,
        semester=f"{p.semester.name} {p.semester.year}",
        priority_rank=p.priority_rank, approval_status=p.approval_status,
        instructor_id=p.instructor_id, instructor_name=p.instructor.name,
    )


def _get_preference(db, scope, preference_id):
    preference = scoped_preferences(db, scope).filter(InstructorPreference.id == preference_id).first()
    if preference is None:
        raise HTTPException(status_code=404, detail="Preference not found")
    return preference


@router.get("", response_model=list[PreferenceAdminOut])
def list_preferences(
    semester_id: Optional[int] = Query(None, description="Defaults to the active semester"),
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    course_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    scope: Scope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    query = scoped_preferences(db, scope)
    if semester_id is None:
        active = db.query(Semester).filter(Semester.is_active.is_(True)).first()
        if active is not None:
            query = query.filter(InstructorPreference.semester_id == active.id)
    else:
        query = query.filter(InstructorPreference.semester_id == semester_id)
    if status:
        query = query.filter(InstructorPreference.approval_status == status)
    if course_id:
        query = query.filter(InstructorPreference.course_id == course_id)
    if instructor_id:
        query = query.filter(InstructorPreference.instructor_id == instructor_id)
    rows = query.order_by(InstructorPreference.course_id, InstructorPreference.priority_rank,
                          InstructorPreference.id).offset(skip).limit(limit).all()
    return [admin_out(p) for p in rows]


def _decide(preference_id, decision, scope, db):
    preference = _get_preference(db, scope, preference_id)
    if preference.semester.is_locked:
        raise HTTPException(status_code=409,
                            detail=f"{preference.semester.name} {preference.semester.year} is locked.")
    before = preference.approval_status
    preference.approval_status = decision
    log_action(
        db, scope.user, f"preference_{decision}", "InstructorPreference", preference.id,
        f"{preference.instructor.name}: {preference.course.code} {preference.course.title} "
        f"({preference.semester.name} {preference.semester.year}, choice #{preference.priority_rank}) "
        f"{before} -> {decision}",
    )
    commit_or_409(db, "Could not save the decision.")
    db.refresh(preference)
    return admin_out(preference)


@router.put("/{preference_id}/approve", response_model=PreferenceAdminOut)
def approve(preference_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    return _decide(preference_id, "approved", scope, db)


@router.put("/{preference_id}/reject", response_model=PreferenceAdminOut)
def reject(preference_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    return _decide(preference_id, "rejected", scope, db)

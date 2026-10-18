"""
Authorization: what each coordinator is allowed to see and change.

  department_coordinator  full read/write inside their own department
  program_coordinator     read-only, limited to their own program (plus the
                          department's instructors, who teach across programs)
  faculty                 only their own profile, history, preferences and
                          allocations (see routers/faculty.py)

Rules that matter:
  * Fail closed: an account with no department/program assigned gets 403, not
    "everything".
  * Scope comes from the database row, never from the token.
  * Out-of-scope records answer 404 (not 403), so their existence is not leaked.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Allocation, Course, Instructor, InstructorPreference, Program, Section, User


@dataclass
class Scope:
    user: User
    department_id: int
    program_id: Optional[int]   # set only for program coordinators
    can_write: bool


def get_scope(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Scope:
    if user.role == "department_coordinator" and user.department_id:
        return Scope(user, user.department_id, None, True)
    if user.role == "program_coordinator" and user.program_id:
        program = db.get(Program, user.program_id)
        if program is not None:
            return Scope(user, program.department_id, program.id, False)
    if user.role == "faculty":
        raise HTTPException(status_code=403, detail="Faculty accounts can only use the /faculty endpoints.")
    raise HTTPException(
        status_code=403,
        detail="Your account has no department or program assigned, so it cannot access data.",
    )


def get_faculty(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Instructor:
    """The instructor record behind a faculty login. Coordinators get 403 here."""
    if user.role != "faculty" or not user.instructor_id:
        raise HTTPException(status_code=403, detail="This endpoint is for faculty accounts only.")
    instructor = db.get(Instructor, user.instructor_id)
    if instructor is None:
        raise HTTPException(status_code=403, detail="Your account is not linked to an instructor.")
    return instructor


def require_writer(scope: Scope = Depends(get_scope)) -> Scope:
    if not scope.can_write:
        raise HTTPException(
            status_code=403,
            detail="Read-only access: only Department Coordinators can make changes.",
        )
    return scope


# --- Scoped queries: every router builds on these, never on a bare db.query() ---

def scoped_programs(db: Session, scope: Scope):
    query = db.query(Program).filter(Program.department_id == scope.department_id)
    if scope.program_id:
        query = query.filter(Program.id == scope.program_id)
    return query


def scoped_courses(db: Session, scope: Scope):
    query = (
        db.query(Course).join(Program, Course.program_id == Program.id)
        .filter(Program.department_id == scope.department_id)
    )
    if scope.program_id:
        query = query.filter(Course.program_id == scope.program_id)
    return query


def scoped_sections(db: Session, scope: Scope):
    query = (
        db.query(Section)
        .join(Course, Section.course_id == Course.id)
        .join(Program, Course.program_id == Program.id)
        .filter(Program.department_id == scope.department_id)
    )
    if scope.program_id:
        query = query.filter(Course.program_id == scope.program_id)
    return query


def scoped_allocations(db: Session, scope: Scope):
    query = (
        db.query(Allocation)
        .join(Section, Allocation.section_id == Section.id)
        .join(Course, Section.course_id == Course.id)
        .join(Program, Course.program_id == Program.id)
        .filter(Program.department_id == scope.department_id)
    )
    if scope.program_id:
        query = query.filter(Course.program_id == scope.program_id)
    return query


def scoped_preferences(db: Session, scope: Scope):
    query = (
        db.query(InstructorPreference)
        .join(Course, InstructorPreference.course_id == Course.id)
        .join(Program, Course.program_id == Program.id)
        .filter(Program.department_id == scope.department_id)
    )
    if scope.program_id:
        query = query.filter(Course.program_id == scope.program_id)
    return query


def scoped_instructors(db: Session, scope: Scope):
    return db.query(Instructor).filter(Instructor.department_id == scope.department_id)


# --- Small helpers shared by the routers ---

def drop_null_fields(data: dict, nullable: tuple = ()) -> dict:
    """For PATCH bodies: ignore explicit nulls on required columns."""
    return {k: v for k, v in data.items() if v is not None or k in nullable}


def commit_or_409(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=message)

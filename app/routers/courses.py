"""
Courses and their prerequisites.

Editing a course's title or requirements clears its embedding, because the old
vector no longer describes the text. Re-run `python -m scripts.generate_embeddings`
to refresh it; until then ranking for that course answers 409.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, commit_or_409, drop_null_fields, get_scope, require_writer,
    scoped_courses, scoped_programs,
)
from app.database import get_db
from app.models import Course, CoursePrerequisite
from app.schemas.academic import (
    CourseCreate, CourseOut, CourseUpdate, PrerequisiteCreate, PrerequisiteOut,
)

router = APIRouter(prefix="/courses", tags=["courses"])


def _get_course(db, scope, course_id):
    course = scoped_courses(db, scope).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _check_program(db, scope, program_id):
    if scoped_programs(db, scope).filter_by(id=program_id).first() is None:
        raise HTTPException(status_code=404, detail="Program not found")


def _code_taken(db, code, exclude_id=None):
    query = db.query(Course).filter(Course.code == code)
    if exclude_id:
        query = query.filter(Course.id != exclude_id)
    return query.first() is not None


@router.get("", response_model=list[CourseOut])
def list_courses(
    program_id: Optional[int] = None,
    q: Optional[str] = Query(None, description="Search code or title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    scope: Scope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    query = scoped_courses(db, scope)
    if program_id:
        query = query.filter(Course.program_id == program_id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Course.code.ilike(like), Course.title.ilike(like)))
    return query.order_by(Course.code).offset(skip).limit(limit).all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return _get_course(db, scope, course_id)


@router.post("", response_model=CourseOut, status_code=201)
def create_course(payload: CourseCreate, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    _check_program(db, scope, payload.program_id)
    if _code_taken(db, payload.code):
        raise HTTPException(status_code=409, detail="A course with this code already exists")
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.patch("/{course_id}", response_model=CourseOut)
def update_course(course_id: int, payload: CourseUpdate,
                  scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    course = _get_course(db, scope, course_id)
    data = drop_null_fields(payload.model_dump(exclude_unset=True), nullable=("requirements_text",))
    if "program_id" in data:
        _check_program(db, scope, data["program_id"])
    if "code" in data and _code_taken(db, data["code"], exclude_id=course.id):
        raise HTTPException(status_code=409, detail="A course with this code already exists")
    for key, value in data.items():
        setattr(course, key, value)
    if "title" in data or "requirements_text" in data:
        course.requirements_embedding = None   # stale: regenerate embeddings
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    course = _get_course(db, scope, course_id)
    # Prerequisite links are just wiring, so they go with the course.
    db.query(CoursePrerequisite).filter(
        or_(CoursePrerequisite.course_id == course.id,
            CoursePrerequisite.prerequisite_course_id == course.id)
    ).delete(synchronize_session=False)
    db.delete(course)
    commit_or_409(db, "This course still has sections or preferences attached. Remove them first.")
    return Response(status_code=204)


# --- Prerequisites ---

def _prerequisite_out(link, prerequisite):
    return PrerequisiteOut(
        course_id=link.course_id,
        prerequisite_course_id=link.prerequisite_course_id,
        prerequisite_code=prerequisite.code,
        prerequisite_title=prerequisite.title,
    )


def _requires(db, start_id, target_id):
    """True if `start_id` already (directly or through others) requires `target_id`."""
    graph = {}
    for link in db.query(CoursePrerequisite).all():
        graph.setdefault(link.course_id, []).append(link.prerequisite_course_id)
    seen, stack = set(), [start_id]
    while stack:
        current = stack.pop()
        if current == target_id:
            return True
        if current not in seen:
            seen.add(current)
            stack.extend(graph.get(current, []))
    return False


@router.get("/{course_id}/prerequisites", response_model=list[PrerequisiteOut])
def list_prerequisites(course_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    course = _get_course(db, scope, course_id)
    links = db.query(CoursePrerequisite).filter_by(course_id=course.id).all()
    return [_prerequisite_out(link, link.prerequisite_course) for link in links]


@router.post("/{course_id}/prerequisites", response_model=PrerequisiteOut, status_code=201)
def add_prerequisite(course_id: int, payload: PrerequisiteCreate,
                     scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    course = _get_course(db, scope, course_id)
    prerequisite = _get_course(db, scope, payload.prerequisite_course_id)
    if prerequisite.id == course.id:
        raise HTTPException(status_code=400, detail="A course cannot be its own prerequisite")
    if db.query(CoursePrerequisite).filter_by(
            course_id=course.id, prerequisite_course_id=prerequisite.id).first():
        raise HTTPException(status_code=409, detail="This prerequisite already exists")
    if _requires(db, prerequisite.id, course.id):
        raise HTTPException(status_code=400, detail="This would create a circular prerequisite chain")
    link = CoursePrerequisite(course_id=course.id, prerequisite_course_id=prerequisite.id)
    db.add(link)
    db.commit()
    return _prerequisite_out(link, prerequisite)


@router.delete("/{course_id}/prerequisites/{prerequisite_course_id}", status_code=204)
def remove_prerequisite(course_id: int, prerequisite_course_id: int,
                        scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    course = _get_course(db, scope, course_id)
    link = db.query(CoursePrerequisite).filter_by(
        course_id=course.id, prerequisite_course_id=prerequisite_course_id).first()
    if link is None:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    db.delete(link)
    db.commit()
    return Response(status_code=204)

"""
Sections of a course in a semester. A locked semester is frozen: its sections
cannot be added, renamed or removed.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, commit_or_409, get_scope, require_writer, scoped_courses, scoped_sections,
)
from app.database import get_db
from app.models import Course, Section, Semester
from app.schemas.academic import SectionCreate, SectionOut, SectionUpdate

router = APIRouter(prefix="/sections", tags=["sections"])


def section_out(section: Section) -> SectionOut:
    return SectionOut(
        id=section.id,
        course_id=section.course_id,
        course_code=section.course.code,
        course_title=section.course.title,
        semester_id=section.semester_id,
        semester=f"{section.semester.name} {section.semester.year}",
        section_label=section.section_label,
    )


def _get_section(db, scope, section_id):
    section = scoped_sections(db, scope).filter(Section.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


def _label_taken(db, course_id, semester_id, label, exclude_id=None):
    query = db.query(Section).filter_by(course_id=course_id, semester_id=semester_id, section_label=label)
    if exclude_id:
        query = query.filter(Section.id != exclude_id)
    return query.first() is not None


def _refuse_if_locked(semester):
    if semester.is_locked:
        raise HTTPException(
            status_code=409,
            detail=f"{semester.name} {semester.year} is locked; its sections cannot be changed.",
        )


@router.get("", response_model=list[SectionOut])
def list_sections(
    semester_id: Optional[int] = None,
    course_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    scope: Scope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    query = scoped_sections(db, scope)
    if semester_id:
        query = query.filter(Section.semester_id == semester_id)
    if course_id:
        query = query.filter(Section.course_id == course_id)
    sections = query.order_by(Course.code, Section.section_label).offset(skip).limit(limit).all()
    return [section_out(s) for s in sections]


@router.get("/{section_id}", response_model=SectionOut)
def get_section(section_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return section_out(_get_section(db, scope, section_id))


@router.post("", response_model=SectionOut, status_code=201)
def create_section(payload: SectionCreate, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    if scoped_courses(db, scope).filter(Course.id == payload.course_id).first() is None:
        raise HTTPException(status_code=404, detail="Course not found")
    semester = db.get(Semester, payload.semester_id)
    if semester is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    _refuse_if_locked(semester)
    if _label_taken(db, payload.course_id, payload.semester_id, payload.section_label):
        raise HTTPException(status_code=409, detail="This section already exists")
    section = Section(**payload.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    return section_out(section)


@router.patch("/{section_id}", response_model=SectionOut)
def update_section(section_id: int, payload: SectionUpdate,
                   scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    section = _get_section(db, scope, section_id)
    _refuse_if_locked(section.semester)
    if _label_taken(db, section.course_id, section.semester_id, payload.section_label, section.id):
        raise HTTPException(status_code=409, detail="This section already exists")
    section.section_label = payload.section_label
    db.commit()
    db.refresh(section)
    return section_out(section)


@router.delete("/{section_id}", status_code=204)
def delete_section(section_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    section = _get_section(db, scope, section_id)
    _refuse_if_locked(section.semester)
    db.delete(section)
    commit_or_409(db, "This section has teaching history, feedback or an allocation attached.")
    return Response(status_code=204)

"""
Allocation endpoints (SRS UC-4). Only Department Coordinators can change
allocations; Program Coordinators can read them.

When an allocation is refused, the response is 409 with a list of EVERY
conflict, so the screen can show them all in one alert:
    {"detail": {"message": "...", "conflicts": [{"code": "...", "message": "..."}]}}
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, get_scope, require_writer, scoped_allocations, scoped_instructors, scoped_sections,
)
from app.database import get_db
from app.models import Allocation, Course, Section, Semester
from app.schemas.allocations import AllocationAdminOut, AllocationCreate
from app.services.allocation import AllocationConflict, allocate, cancel

router = APIRouter(prefix="/allocations", tags=["allocations"])


def allocation_out(a: Allocation) -> AllocationAdminOut:
    section = a.section
    return AllocationAdminOut(
        id=a.id, section_id=section.id,
        course_code=section.course.code, course_title=section.course.title,
        section_label=section.section_label,
        semester=f"{section.semester.name} {section.semester.year}",
        instructor_id=a.instructor_id, instructor_name=a.instructor.name,
        score=a.score, explanation=a.explanation, status=a.status, allocated_at=a.allocated_at,
    )


def conflict_error(verb: str, conflicts) -> HTTPException:
    n = len(conflicts)
    return HTTPException(status_code=409, detail={
        "message": f"Cannot {verb}: {n} conflict{'s' if n != 1 else ''} must be resolved first.",
        "conflicts": [{"code": c.code, "message": c.message} for c in conflicts],
    })


@router.get("", response_model=list[AllocationAdminOut])
def list_allocations(
    semester_id: Optional[int] = Query(None, description="Defaults to the active semester"),
    section_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    status: str = Query("confirmed", pattern="^(confirmed|cancelled|all)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    scope: Scope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    query = scoped_allocations(db, scope)
    if section_id:
        query = query.filter(Allocation.section_id == section_id)
    elif semester_id is not None:
        query = query.filter(Section.semester_id == semester_id)
    else:
        active = db.query(Semester).filter(Semester.is_active.is_(True)).first()
        if active is not None:
            query = query.filter(Section.semester_id == active.id)
    if instructor_id:
        query = query.filter(Allocation.instructor_id == instructor_id)
    if status != "all":
        query = query.filter(Allocation.status == status)
    rows = query.order_by(Course.code, Section.section_label, Allocation.id).offset(skip).limit(limit).all()
    return [allocation_out(a) for a in rows]


@router.post("", response_model=AllocationAdminOut, status_code=201)
def create_allocation(payload: AllocationCreate, scope: Scope = Depends(require_writer),
                      db: Session = Depends(get_db)):
    section = scoped_sections(db, scope).filter(Section.id == payload.section_id).first()
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")
    instructor = scoped_instructors(db, scope).filter_by(id=payload.instructor_id).first()
    if instructor is None:
        raise HTTPException(status_code=404, detail="Instructor not found")

    try:
        allocation = allocate(db, scope.user, section, instructor)
        db.commit()
    except AllocationConflict as error:
        db.rollback()
        raise conflict_error("allocate", error.conflicts)
    except IntegrityError:
        # The database's own guarantee: someone confirmed this section a moment ago.
        db.rollback()
        raise HTTPException(status_code=409, detail={
            "message": "Cannot allocate: 1 conflict must be resolved first.",
            "conflicts": [{"code": "already_allocated",
                           "message": "This section was just allocated by someone else. Refresh to see who."}],
        })
    except RuntimeError as error:        # ranking settings not seeded
        db.rollback()
        raise HTTPException(status_code=503, detail=str(error))
    db.refresh(allocation)
    return allocation_out(allocation)


@router.post("/{allocation_id}/cancel", response_model=AllocationAdminOut)
def cancel_allocation(allocation_id: int, scope: Scope = Depends(require_writer),
                      db: Session = Depends(get_db)):
    allocation = scoped_allocations(db, scope).filter(Allocation.id == allocation_id).first()
    if allocation is None:
        raise HTTPException(status_code=404, detail="Allocation not found")
    try:
        cancel(db, scope.user, allocation)
        db.commit()
    except AllocationConflict as error:
        db.rollback()
        raise conflict_error("cancel", error.conflicts)
    db.refresh(allocation)
    return allocation_out(allocation)

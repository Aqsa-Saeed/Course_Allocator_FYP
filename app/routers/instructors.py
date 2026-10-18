"""
Instructors. Department Coordinators manage their own department's instructors;
Program Coordinators can read them (instructors teach across programs).

Editing an instructor's specializations clears their embedding; re-run
`python -m scripts.generate_embeddings` to refresh it.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, commit_or_409, drop_null_fields, get_scope, require_writer, scoped_instructors,
)
from app.database import get_db
from app.models import Instructor
from app.schemas.academic import InstructorCreate, InstructorOut, InstructorUpdate

router = APIRouter(prefix="/instructors", tags=["instructors"])

NULLABLE = ("academic_rank", "highest_qualification", "qualifications_text")


def _get_instructor(db, scope, instructor_id):
    instructor = scoped_instructors(db, scope).filter(Instructor.id == instructor_id).first()
    if instructor is None:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return instructor


def _email_taken(db, email, exclude_id=None):
    query = db.query(Instructor).filter(Instructor.email == email)
    if exclude_id:
        query = query.filter(Instructor.id != exclude_id)
    return query.first() is not None


@router.get("", response_model=list[InstructorOut])
def list_instructors(
    status: Optional[str] = Query(None, pattern="^(active|on_leave)$"),
    q: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    scope: Scope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    query = scoped_instructors(db, scope)
    if status:
        query = query.filter(Instructor.status == status)
    if q:
        query = query.filter(Instructor.name.ilike(f"%{q}%"))
    return query.order_by(Instructor.name).offset(skip).limit(limit).all()


@router.get("/{instructor_id}", response_model=InstructorOut)
def get_instructor(instructor_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return _get_instructor(db, scope, instructor_id)


@router.post("", response_model=InstructorOut, status_code=201)
def create_instructor(payload: InstructorCreate, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    email = payload.email.lower()
    if _email_taken(db, email):
        raise HTTPException(status_code=409, detail="An instructor with this email already exists")
    data = payload.model_dump()
    data["email"] = email
    instructor = Instructor(**data, department_id=scope.department_id)
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    return instructor


@router.patch("/{instructor_id}", response_model=InstructorOut)
def update_instructor(instructor_id: int, payload: InstructorUpdate,
                      scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    instructor = _get_instructor(db, scope, instructor_id)
    data = drop_null_fields(payload.model_dump(exclude_unset=True), nullable=NULLABLE)
    if "email" in data:
        data["email"] = data["email"].lower()
        if _email_taken(db, data["email"], exclude_id=instructor.id):
            raise HTTPException(status_code=409, detail="An instructor with this email already exists")
    for key, value in data.items():
        setattr(instructor, key, value)
    if "qualifications_text" in data:
        instructor.qualifications_embedding = None   # stale: regenerate embeddings
    db.commit()
    db.refresh(instructor)
    return instructor


@router.delete("/{instructor_id}", status_code=204)
def delete_instructor(instructor_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    instructor = _get_instructor(db, scope, instructor_id)
    db.delete(instructor)
    commit_or_409(
        db,
        "This instructor has teaching history, feedback, preferences or allocations. "
        "Set their status to on_leave instead of deleting them.",
    )
    return Response(status_code=204)

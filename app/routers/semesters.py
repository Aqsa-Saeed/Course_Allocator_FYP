"""
Semesters are shared across the whole university, so every coordinator can read
them, but only Department Coordinators can change them. At most one semester is
active at a time: activating one deactivates the others.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, commit_or_409, drop_null_fields, get_scope, require_writer,
)
from app.database import get_db
from app.models import Semester
from app.schemas.academic import SemesterCreate, SemesterOut, SemesterUpdate

router = APIRouter(prefix="/semesters", tags=["semesters"])


def _get_semester(db, semester_id):
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    return semester


def _exists(db, name, year, exclude_id=None):
    query = db.query(Semester).filter_by(name=name, year=year)
    if exclude_id:
        query = query.filter(Semester.id != exclude_id)
    return query.first() is not None


def _make_only_active(db, semester):
    db.query(Semester).filter(Semester.id != semester.id).update({Semester.is_active: False})


@router.get("", response_model=list[SemesterOut])
def list_semesters(scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return db.query(Semester).order_by(Semester.year.desc(), Semester.name).all()


@router.get("/active", response_model=SemesterOut)
def active_semester(scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    semester = db.query(Semester).filter(Semester.is_active.is_(True)).first()
    if semester is None:
        raise HTTPException(status_code=404, detail="No semester is currently active")
    return semester


@router.get("/{semester_id}", response_model=SemesterOut)
def get_semester(semester_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return _get_semester(db, semester_id)


@router.post("", response_model=SemesterOut, status_code=201)
def create_semester(payload: SemesterCreate, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    if _exists(db, payload.name, payload.year):
        raise HTTPException(status_code=409, detail="This semester already exists")
    semester = Semester(**payload.model_dump())
    db.add(semester)
    db.flush()
    if semester.is_active:
        _make_only_active(db, semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.patch("/{semester_id}", response_model=SemesterOut)
def update_semester(semester_id: int, payload: SemesterUpdate,
                    scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    semester = _get_semester(db, semester_id)
    data = drop_null_fields(payload.model_dump(exclude_unset=True), nullable=("start_date", "end_date"))
    new_name, new_year = data.get("name", semester.name), data.get("year", semester.year)
    if (new_name, new_year) != (semester.name, semester.year) and _exists(db, new_name, new_year, semester.id):
        raise HTTPException(status_code=409, detail="This semester already exists")
    for key, value in data.items():
        setattr(semester, key, value)
    if data.get("is_active"):
        _make_only_active(db, semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.delete("/{semester_id}", status_code=204)
def delete_semester(semester_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    db.delete(_get_semester(db, semester_id))
    commit_or_409(db, "This semester still has sections, workload or preferences attached.")
    return Response(status_code=204)

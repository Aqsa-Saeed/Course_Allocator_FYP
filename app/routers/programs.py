from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.access import (
    Scope, commit_or_409, drop_null_fields, get_scope, require_writer, scoped_programs,
)
from app.database import get_db
from app.models import Program
from app.schemas.academic import ProgramCreate, ProgramOut, ProgramUpdate

router = APIRouter(prefix="/programs", tags=["programs"])


def _get_program(db, scope, program_id):
    program = scoped_programs(db, scope).filter(Program.id == program_id).first()
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


def _name_taken(db, scope, name, exclude_id=None):
    query = db.query(Program).filter(
        Program.department_id == scope.department_id, Program.name == name)
    if exclude_id:
        query = query.filter(Program.id != exclude_id)
    return query.first() is not None


@router.get("", response_model=list[ProgramOut])
def list_programs(scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return scoped_programs(db, scope).order_by(Program.name).all()


@router.get("/{program_id}", response_model=ProgramOut)
def get_program(program_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return _get_program(db, scope, program_id)


@router.post("", response_model=ProgramOut, status_code=201)
def create_program(payload: ProgramCreate, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    if _name_taken(db, scope, payload.name):
        raise HTTPException(status_code=409, detail="A program with this name already exists")
    program = Program(name=payload.name, department_id=scope.department_id)
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.patch("/{program_id}", response_model=ProgramOut)
def update_program(program_id: int, payload: ProgramUpdate,
                   scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    program = _get_program(db, scope, program_id)
    data = drop_null_fields(payload.model_dump(exclude_unset=True))
    if "name" in data and _name_taken(db, scope, data["name"], exclude_id=program.id):
        raise HTTPException(status_code=409, detail="A program with this name already exists")
    for key, value in data.items():
        setattr(program, key, value)
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=204)
def delete_program(program_id: int, scope: Scope = Depends(require_writer), db: Session = Depends(get_db)):
    program = _get_program(db, scope, program_id)
    db.delete(program)
    commit_or_409(db, "This program still has courses or users attached. Remove or move them first.")
    return Response(status_code=204)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.access import get_scope
from app.core.deps import get_current_user
from app.database import get_db
from app.models import Department, Instructor, Program, User
from app.schemas.academic import DepartmentOut, MeOut, ProgramOut

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Who am I, and what can I see? The frontend uses this to decide what to show."""
    if user.role == "faculty":
        instructor = db.get(Instructor, user.instructor_id) if user.instructor_id else None
        if instructor is None:
            raise HTTPException(status_code=403, detail="Your account is not linked to an instructor.")
        return MeOut(
            id=user.id, username=user.username, email=user.email, role=user.role,
            can_write=False,
            department=DepartmentOut.model_validate(db.get(Department, instructor.department_id)),
            program=None,
            instructor_id=instructor.id,
        )

    scope = get_scope(user, db)   # raises 403 for accounts with no scope
    program = db.get(Program, scope.program_id) if scope.program_id else None
    return MeOut(
        id=user.id, username=user.username, email=user.email, role=user.role,
        can_write=scope.can_write,
        department=DepartmentOut.model_validate(db.get(Department, scope.department_id)),
        program=ProgramOut.model_validate(program) if program else None,
    )

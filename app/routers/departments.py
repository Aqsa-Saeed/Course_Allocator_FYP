from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.access import Scope, get_scope
from app.database import get_db
from app.models import Department
from app.schemas.academic import DepartmentOut

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return db.query(Department).filter(Department.id == scope.department_id).all()


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: int, scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    if department_id != scope.department_id:
        raise HTTPException(status_code=404, detail="Department not found")
    return db.get(Department, department_id)

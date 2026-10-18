"""
Read the audit trail (SRS 5.2). Department Coordinators see the entries made by
people in their own department: coordinators and faculty.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.core.access import Scope, require_writer
from app.database import get_db
from app.models import AuditLog, Instructor, User
from app.schemas.preferences import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    scope: Scope = Depends(require_writer),
    db: Session = Depends(get_db),
):
    actor = aliased(User)
    query = (
        db.query(AuditLog, actor.username)
        .join(actor, AuditLog.actor_user_id == actor.id)
        .outerjoin(Instructor, actor.instructor_id == Instructor.id)
        .filter(or_(actor.department_id == scope.department_id,
                    Instructor.department_id == scope.department_id))
    )
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    rows = query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).offset(skip).limit(limit).all()
    return [
        AuditLogOut(id=log.id, timestamp=log.timestamp, action=log.action, entity_type=log.entity_type,
                    entity_id=log.entity_id, actor_username=username, details=log.details)
        for log, username in rows
    ]

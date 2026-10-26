"""Access control, built on the app's own auth (app.core.deps / app.core.access).

- Faculty cannot use document chat at all (it contains feedback about named colleagues).
- Coordinators only ever see documents from their own department (same boundary as get_scope).
- Upload and delete additionally need can_write, exactly like the rest of the app.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.access import get_scope
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User


@dataclass
class RagScope:
    user_id: int
    department_id: int
    can_write: bool


def get_rag_scope(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RagScope:
    if user.role == "faculty":
        raise HTTPException(status_code=403, detail="Document chat is only available to coordinators.")
    scope = get_scope(user, db)  # raises 403 for accounts with no scope, like /me does
    return RagScope(user_id=user.id, department_id=scope.department_id, can_write=bool(scope.can_write))


def require_rag_write(scope: RagScope = Depends(get_rag_scope)) -> RagScope:
    if not scope.can_write:
        raise HTTPException(status_code=403, detail="Your account has read-only access.")
    return scope

"""
Audit trail (SRS 5.2): every decision records what changed, who changed it
and when. The entry is added to the SAME database transaction as the change,
so either both are saved or neither is (SRS 6.1: no partial saves).
"""

from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_action(db: Session, user: User, action: str, entity_type: str,
               entity_id: int, details: str = None) -> None:
    db.add(AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=user.id if user else None,
        details=details,
    ))
    # No commit here on purpose: the caller commits the change and the log together.

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class AuditLog(Base):
    """
    SRS 5.2: every allocation change must record what was changed,
    who changed it, and when — kept separate from Allocation itself
    so history survives even if the allocation row is later modified.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    action = Column(String(50), nullable=False)       # e.g. "allocation_created", "preference_approved"
    entity_type = Column(String(50), nullable=False)   # e.g. "Allocation", "InstructorPreference"
    entity_id = Column(Integer, nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(Text, nullable=True)               # free-text / JSON-as-text description
    timestamp = Column(DateTime, default=datetime.utcnow)

    actor = relationship("User")

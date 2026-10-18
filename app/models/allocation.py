from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import relationship

from .base import Base


class Allocation(Base):
    """
    The finalized assignment of an instructor to a Section (SRS UC-4).

    A cancelled allocation stays in the table as history; only a 'confirmed'
    one counts. The partial unique index below lets the DATABASE guarantee that
    a section never has two confirmed allocations, even if two coordinators
    press the button at the same moment.
    """
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)

    score = Column(Float, nullable=True)          # the ranking score when it was confirmed
    explanation = Column(Text, nullable=True)     # the ranking explanation when it was confirmed
    status = Column(String(20), default="confirmed")  # confirmed | cancelled

    allocated_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="allocations")
    instructor = relationship("Instructor", back_populates="allocations")

    __table_args__ = (
        Index(
            "uq_one_confirmed_allocation_per_section",
            "section_id",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
        ),
    )

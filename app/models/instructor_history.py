from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class InstructorHistory(Base):
    """Ground-truth record: this instructor taught this section."""
    __tablename__ = "instructor_history"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)

    instructor = relationship("Instructor", back_populates="history")
    section = relationship("Section", back_populates="instructor_history")

    __table_args__ = (
        UniqueConstraint("instructor_id", "section_id", name="uq_instructor_section_history"),
    )

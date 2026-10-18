from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Section(Base):
    """
    A course can have multiple sections per semester, each independently
    assignable to an instructor. This is what Allocation actually targets —
    not Course directly.
    """
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    section_label = Column(String(10), nullable=False)   # e.g. "A", "B", "01"

    course = relationship("Course", back_populates="sections")
    semester = relationship("Semester", back_populates="sections")
    instructor_history = relationship("InstructorHistory", back_populates="section")
    feedback_scores = relationship("FeedbackScore", back_populates="section")
    # Several rows over time: a cancelled allocation is kept as history
    allocations = relationship("Allocation", back_populates="section")

    __table_args__ = (
        UniqueConstraint("course_id", "semester_id", "section_label",
                          name="uq_section"),
    )

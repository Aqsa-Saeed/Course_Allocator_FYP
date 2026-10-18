from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class InstructorPreference(Base):
    """
    An instructor's submitted preference to teach a Course (not a specific
    Section — sections get assigned afterward by the coordinator).
    """
    __tablename__ = "instructor_preferences"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    priority_rank = Column(Integer, nullable=False, default=1)  # 1 = top choice
    approval_status = Column(String(20), nullable=False, default="pending")  # pending | approved | rejected

    instructor = relationship("Instructor", back_populates="preferences")
    course = relationship("Course", back_populates="preferences")
    semester = relationship("Semester", back_populates="preferences")

    __table_args__ = (
        UniqueConstraint("instructor_id", "course_id", "semester_id", name="uq_preference"),
    )

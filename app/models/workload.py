from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Workload(Base):
    __tablename__ = "workload"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    course_count = Column(Integer, nullable=False, default=0)
    total_credit_hours = Column(Integer, nullable=False, default=0)

    instructor = relationship("Instructor", back_populates="workload_entries")
    semester = relationship("Semester", back_populates="workload_entries")

    __table_args__ = (
        UniqueConstraint("instructor_id", "semester_id", name="uq_workload_term"),
    )

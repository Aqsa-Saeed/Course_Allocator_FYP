from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base, EMBEDDING_DIM


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)   # e.g. "CS401"
    title = Column(String(200), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    credit_hours = Column(Integer, nullable=False, default=3)

    requirements_text = Column(Text, nullable=True)
    requirements_embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    program = relationship("Program", back_populates="courses")
    sections = relationship("Section", back_populates="course")
    preferences = relationship("InstructorPreference", back_populates="course")

    # prerequisites THIS course requires
    prerequisites = relationship(
        "CoursePrerequisite",
        foreign_keys="CoursePrerequisite.course_id",
        back_populates="course",
    )

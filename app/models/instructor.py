from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base, EMBEDDING_DIM


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    academic_rank = Column(String(50), nullable=True)           # e.g. "Lecturer", "Assistant Professor"
    highest_qualification = Column(String(50), nullable=True)   # e.g. "PhD", "MS/M.Phil"
    # "active" or "on_leave" — lets policy checks skip instructors who are unavailable
    status = Column(String(20), nullable=False, default="active", server_default="active")

    qualifications_text = Column(Text, nullable=True)
    qualifications_embedding = Column(Vector(EMBEDDING_DIM), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="instructors")
    history = relationship("InstructorHistory", back_populates="instructor")
    feedback_scores = relationship("FeedbackScore", back_populates="instructor")
    workload_entries = relationship("Workload", back_populates="instructor")
    preferences = relationship("InstructorPreference", back_populates="instructor")
    allocations = relationship("Allocation", back_populates="instructor")

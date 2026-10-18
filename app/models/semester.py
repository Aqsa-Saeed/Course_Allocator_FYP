from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship

from .base import Base


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)   # e.g. "Fall"
    year = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    sections = relationship("Section", back_populates="semester")
    workload_entries = relationship("Workload", back_populates="semester")
    preferences = relationship("InstructorPreference", back_populates="semester")

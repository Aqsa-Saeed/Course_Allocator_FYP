from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """
    Someone who logs in.
      role = 'department_coordinator'  department_id set; full access to that department
      role = 'program_coordinator'     program_id set; read-only access to that program
      role = 'faculty'                 instructor_id set; sees and edits only their own data
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="department_coordinator")
    is_active = Column(Boolean, default=True)

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    # One login per instructor (faculty role only)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="users")
    program = relationship("Program", back_populates="users")
    instructor = relationship("Instructor")

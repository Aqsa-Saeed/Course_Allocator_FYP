from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)

    programs = relationship("Program", back_populates="department")
    instructors = relationship("Instructor", back_populates="department")
    users = relationship("User", back_populates="department")

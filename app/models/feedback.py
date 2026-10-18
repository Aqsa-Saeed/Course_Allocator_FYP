from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class FeedbackScore(Base):
    __tablename__ = "feedback_scores"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    score = Column(Float, nullable=False)  # e.g. 0-5 scale

    instructor = relationship("Instructor", back_populates="feedback_scores")
    section = relationship("Section", back_populates="feedback_scores")

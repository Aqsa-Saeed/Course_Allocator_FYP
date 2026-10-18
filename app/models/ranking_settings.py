from sqlalchemy import Column, Integer, Float

from .base import Base


class RankingSettings(Base):
    """
    Single-row, admin-adjustable config: the scoring weights and the policy
    thresholds. Keeping them in a table (not in code) means they are visible
    and tunable. Weights do not need to add up to 1; the ranking engine
    normalizes them.
    """
    __tablename__ = "ranking_settings"

    id = Column(Integer, primary_key=True)

    weight_content_match = Column(Float, nullable=False, default=0.25)  # embedding similarity
    weight_history = Column(Float, nullable=False, default=0.20)        # taught this/related courses
    weight_recency = Column(Float, nullable=False, default=0.10)        # how recently
    weight_feedback = Column(Float, nullable=False, default=0.20)       # smoothed student feedback
    weight_preference = Column(Float, nullable=False, default=0.15, server_default="0.15")
    weight_workload = Column(Float, nullable=False, default=0.10, server_default="0.10")

    # Policy thresholds (SRS: Policy Validation Checks)
    min_feedback_score = Column(Float, nullable=False, default=2.5)
    max_courses_per_instructor = Column(Integer, nullable=False, default=4)

from typing import Optional

from pydantic import BaseModel, Field, model_validator

WEIGHT_FIELDS = (
    "weight_content_match", "weight_history", "weight_recency",
    "weight_feedback", "weight_preference", "weight_workload",
)


class RankingSettingsOut(BaseModel):
    weight_content_match: float
    weight_history: float
    weight_recency: float
    weight_feedback: float
    weight_preference: float
    weight_workload: float
    min_feedback_score: float
    max_courses_per_instructor: int


class RankingSettingsUpdate(BaseModel):
    """Every field is optional: send only what you want to change."""
    weight_content_match: Optional[float] = Field(None, ge=0, le=1)
    weight_history: Optional[float] = Field(None, ge=0, le=1)
    weight_recency: Optional[float] = Field(None, ge=0, le=1)
    weight_feedback: Optional[float] = Field(None, ge=0, le=1)
    weight_preference: Optional[float] = Field(None, ge=0, le=1)
    weight_workload: Optional[float] = Field(None, ge=0, le=1)
    min_feedback_score: Optional[float] = Field(None, ge=0, le=5)
    max_courses_per_instructor: Optional[int] = Field(None, ge=1, le=10)

    @model_validator(mode="after")
    def not_empty(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one setting to change")
        return self

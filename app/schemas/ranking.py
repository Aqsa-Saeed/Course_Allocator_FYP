from typing import Optional

from pydantic import BaseModel


class ComponentOut(BaseModel):
    key: str
    label: str
    value: float          # the 0..1 signal
    weight: float         # normalized weight
    contribution: float   # value * weight


class CandidateOut(BaseModel):
    rank: int
    instructor_id: int
    instructor_name: str
    academic_rank: Optional[str] = None
    score: float
    components: list[ComponentOut]
    explanation: str


class ExcludedOut(BaseModel):
    instructor_id: int
    instructor_name: str
    reason: str


class RecommendationOut(BaseModel):
    section_id: int
    course_code: str
    course_title: str
    section_label: str
    semester: str
    candidates: list[CandidateOut]
    excluded: list[ExcludedOut]
    message: Optional[str] = None

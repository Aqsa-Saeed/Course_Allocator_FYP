from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AllocationCreate(BaseModel):
    section_id: int
    instructor_id: int


class AllocationAdminOut(BaseModel):
    id: int
    section_id: int
    course_code: str
    course_title: str
    section_label: str
    semester: str
    instructor_id: int
    instructor_name: str
    score: Optional[float] = None
    explanation: Optional[str] = None
    status: str
    allocated_at: Optional[datetime] = None

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

MAX_PREFERENCES = 5


class PreferenceCreate(BaseModel):
    course_id: int
    priority_rank: Optional[int] = Field(None, ge=1, le=MAX_PREFERENCES,
                                         description="1 = first choice. Omit to take the next free rank.")


class PreferenceOut(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_title: str
    semester: str
    priority_rank: int
    approval_status: str


class PreferenceAdminOut(PreferenceOut):
    instructor_id: int
    instructor_name: str


class FacultyProfileOut(BaseModel):
    id: int
    name: str
    email: str
    department: str
    academic_rank: Optional[str] = None
    highest_qualification: Optional[str] = None
    status: str
    qualifications_text: Optional[str] = None


class TeachingHistoryOut(BaseModel):
    course_code: str
    course_title: str
    section_label: str
    semester: str
    feedback_score: Optional[float] = None   # empty while the semester is in progress


class OfferedCourseOut(BaseModel):
    course_id: int
    code: str
    title: str
    credit_hours: int
    sections_offered: int
    requested: bool     # True if I have already asked to teach it


class AllocationOut(BaseModel):
    id: int
    course_code: str
    course_title: str
    section_label: str
    semester: str
    status: str
    allocated_at: Optional[datetime] = None


class AuditLogOut(BaseModel):
    id: int
    timestamp: Optional[datetime] = None
    action: str
    entity_type: str
    entity_id: int
    actor_username: Optional[str] = None
    details: Optional[str] = None


Decision = Literal["approved", "rejected"]

"""Request/response shapes for the academic records. Embeddings are never exposed."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Departments / programs ---
class DepartmentOut(ORM):
    id: int
    name: str


class ProgramCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class ProgramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)


class ProgramOut(ORM):
    id: int
    name: str
    department_id: int


# --- Semesters ---
TermName = Literal["Spring", "Fall"]


class SemesterCreate(BaseModel):
    name: TermName
    year: int = Field(ge=2000, le=2100)
    is_active: bool = False
    is_locked: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SemesterUpdate(BaseModel):
    name: Optional[TermName] = None
    year: Optional[int] = Field(None, ge=2000, le=2100)
    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SemesterOut(ORM):
    id: int
    name: str
    year: int
    is_active: bool
    is_locked: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# --- Courses ---
class CourseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    title: str = Field(min_length=2, max_length=200)
    program_id: int
    credit_hours: int = Field(3, ge=1, le=6)
    requirements_text: Optional[str] = None


class CourseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    program_id: Optional[int] = None
    credit_hours: Optional[int] = Field(None, ge=1, le=6)
    requirements_text: Optional[str] = None


class CourseOut(ORM):
    id: int
    code: str
    title: str
    program_id: int
    credit_hours: int
    requirements_text: Optional[str] = None


class PrerequisiteCreate(BaseModel):
    prerequisite_course_id: int


class PrerequisiteOut(BaseModel):
    course_id: int
    prerequisite_course_id: int
    prerequisite_code: str
    prerequisite_title: str


# --- Sections ---
class SectionCreate(BaseModel):
    course_id: int
    semester_id: int
    section_label: str = Field(min_length=1, max_length=10)


class SectionUpdate(BaseModel):
    section_label: str = Field(min_length=1, max_length=10)


class SectionOut(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_title: str
    semester_id: int
    semester: str            # e.g. "Spring 2027"
    section_label: str


# --- Instructors ---
InstructorStatus = Literal["active", "on_leave"]


class InstructorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    academic_rank: Optional[str] = Field(None, max_length=50)
    highest_qualification: Optional[str] = Field(None, max_length=50)
    status: InstructorStatus = "active"
    qualifications_text: Optional[str] = None


class InstructorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    academic_rank: Optional[str] = Field(None, max_length=50)
    highest_qualification: Optional[str] = Field(None, max_length=50)
    status: Optional[InstructorStatus] = None
    qualifications_text: Optional[str] = None


class InstructorOut(ORM):
    id: int
    name: str
    email: str
    department_id: int
    academic_rank: Optional[str] = None
    highest_qualification: Optional[str] = None
    status: str
    qualifications_text: Optional[str] = None


# --- Current user ---
class MeOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    can_write: bool
    department: DepartmentOut
    program: Optional[ProgramOut] = None
    instructor_id: Optional[int] = None   # set for faculty accounts

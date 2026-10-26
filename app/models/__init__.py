"""
Importing every model here, once, resolves the string-based
relationship() references and is what Alembic's env.py imports
to see the full schema. If a model file isn't imported here,
its table silently won't show up in migrations.
"""

from .base import Base
from .department import Department
from .program import Program
from .semester import Semester
from .course import Course
from .section import Section
from .course_prerequisite import CoursePrerequisite
from .instructor import Instructor
from .user import User
from .instructor_history import InstructorHistory
from .feedback import FeedbackScore
from .workload import Workload
from .preference import InstructorPreference
from .allocation import Allocation
from .audit_log import AuditLog
from .ranking_settings import RankingSettings
from .password_reset import PasswordResetCode  # noqa: F401


__all__ = [
    "Base",
    "Department",
    "Program",
    "Semester",
    "Course",
    "Section",
    "CoursePrerequisite",
    "Instructor",
    "User",
    "InstructorHistory",
    "FeedbackScore",
    "Workload",
    "InstructorPreference",
    "Allocation",
    "AuditLog",
    "RankingSettings",
]

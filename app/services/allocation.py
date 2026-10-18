"""
Allocation (SRS UC-4): a coordinator confirms an instructor for a section.

Every rule below BLOCKS the allocation: the coordinator is shown ALL the
conflicts at once and must resolve them (pick someone else, end the leave,
raise the limit, cancel the other allocation...) before it can be saved.
There is no override.

  already_allocated   the section already has a confirmed instructor
  semester_locked     the semester is frozen
  on_leave            the instructor is on leave
  workload_cap        the instructor already has the maximum number of sections
  low_feedback        the instructor's smoothed feedback is below the minimum

The checks run again at the moment of saving, inside the transaction and with
the instructor and section rows locked. So if two coordinators work at once,
the second one sees the first one's allocation instead of both succeeding.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Allocation, Instructor, Section, User
from app.services.audit import log_action
from app.services.ranking import policy_violations, rank_instructors


@dataclass
class Conflict:
    code: str
    message: str


class AllocationConflict(Exception):
    def __init__(self, conflicts: list):
        super().__init__("; ".join(c.message for c in conflicts))
        self.conflicts = conflicts


def find_conflicts(db: Session, section: Section, instructor: Instructor) -> list:
    conflicts = []
    semester = section.semester

    if semester.is_locked:
        conflicts.append(Conflict("semester_locked",
                                  f"{semester.name} {semester.year} is locked, so its allocations cannot be changed."))

    existing = db.query(Allocation).filter_by(section_id=section.id, status="confirmed").first()
    if existing is not None:
        conflicts.append(Conflict(
            "already_allocated",
            f"{section.course.code} section {section.section_label} is already allocated to "
            f"{existing.instructor.name}. Cancel that allocation first.",
        ))

    for code, message in policy_violations(db, section, instructor):
        conflicts.append(Conflict(code, f"{instructor.name}: {message}"))
    return conflicts


def _ranking_snapshot(db: Session, section: Section, instructor: Instructor):
    """The score and explanation the ranking gave, kept with the allocation as the reason for it."""
    try:
        result = rank_instructors(db, section, limit=500)
    except (ValueError, RuntimeError):
        return None, None      # e.g. the course has no embedding yet: allocate without a score
    for candidate in result.candidates:
        if candidate.instructor.id == instructor.id:
            return candidate.score, candidate.explanation
    return None, None


def allocate(db: Session, user: User, section: Section, instructor: Instructor) -> Allocation:
    """Confirm the allocation. The CALLER commits, so the audit entry saves with it."""
    # Lock both rows (always in the same order) so concurrent requests are handled one at a time.
    db.query(Instructor).filter_by(id=instructor.id).with_for_update().one()
    db.query(Section).filter_by(id=section.id).with_for_update().one()

    conflicts = find_conflicts(db, section, instructor)
    if conflicts:
        raise AllocationConflict(conflicts)

    score, explanation = _ranking_snapshot(db, section, instructor)
    allocation = Allocation(section_id=section.id, instructor_id=instructor.id,
                            score=score, explanation=explanation, status="confirmed")
    db.add(allocation)
    db.flush()
    log_action(
        db, user, "allocation_confirmed", "Allocation", allocation.id,
        f"{instructor.name} allocated to {section.course.code} {section.course.title}, "
        f"section {section.section_label} ({section.semester.name} {section.semester.year})"
        + (f", ranking score {score:.3f}" if score is not None else ""),
    )
    return allocation


def cancel(db: Session, user: User, allocation: Allocation) -> Allocation:
    """Cancel a confirmed allocation (kept as history). The CALLER commits."""
    section = allocation.section
    if section.semester.is_locked:
        raise AllocationConflict([Conflict(
            "semester_locked",
            f"{section.semester.name} {section.semester.year} is locked, so its allocations cannot be changed.")])
    if allocation.status != "confirmed":
        raise AllocationConflict([Conflict("not_confirmed", "This allocation is already cancelled.")])

    allocation.status = "cancelled"
    log_action(
        db, user, "allocation_cancelled", "Allocation", allocation.id,
        f"{allocation.instructor.name} removed from {section.course.code} section "
        f"{section.section_label} ({section.semester.name} {section.semester.year})",
    )
    return allocation

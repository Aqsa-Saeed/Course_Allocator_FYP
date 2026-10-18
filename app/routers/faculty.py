"""
The faculty page: an instructor sees and manages only their OWN data.
Every query here is filtered by the instructor behind the login, never by an
id the client sends, so there is no way to look at someone else's records.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.access import commit_or_409, get_faculty
from app.core.deps import get_current_user
from app.database import get_db
from app.models import (
    Allocation, Course, Department, FeedbackScore, Instructor, InstructorHistory,
    InstructorPreference, Program, Section, Semester, User,
)
from app.schemas.preferences import (
    MAX_PREFERENCES, AllocationOut, FacultyProfileOut, OfferedCourseOut, PreferenceCreate,
    PreferenceOut, TeachingHistoryOut,
)
from app.services.audit import log_action

router = APIRouter(prefix="/faculty/me", tags=["faculty"])


def preference_out(p: InstructorPreference) -> PreferenceOut:
    return PreferenceOut(
        id=p.id, course_id=p.course_id, course_code=p.course.code, course_title=p.course.title,
        semester=f"{p.semester.name} {p.semester.year}",
        priority_rank=p.priority_rank, approval_status=p.approval_status,
    )


def _term_key(semester):
    return (semester.year, 0 if semester.name == "Spring" else 1)


def _open_semester(db):
    semester = db.query(Semester).filter(Semester.is_active.is_(True)).first()
    if semester is None:
        raise HTTPException(status_code=409, detail="No semester is open for preferences right now.")
    if semester.is_locked:
        raise HTTPException(status_code=409,
                            detail=f"Preferences for {semester.name} {semester.year} are closed.")
    return semester


@router.get("", response_model=FacultyProfileOut)
def my_profile(instructor: Instructor = Depends(get_faculty), db: Session = Depends(get_db)):
    return FacultyProfileOut(
        id=instructor.id, name=instructor.name, email=instructor.email,
        department=db.get(Department, instructor.department_id).name,
        academic_rank=instructor.academic_rank,
        highest_qualification=instructor.highest_qualification,
        status=instructor.status,
        qualifications_text=instructor.qualifications_text,
    )


@router.get("/history", response_model=list[TeachingHistoryOut])
def my_teaching_history(instructor: Instructor = Depends(get_faculty), db: Session = Depends(get_db)):
    rows = (
        db.query(Section, FeedbackScore.score)
        .join(InstructorHistory, InstructorHistory.section_id == Section.id)
        .outerjoin(FeedbackScore, (FeedbackScore.section_id == Section.id)
                   & (FeedbackScore.instructor_id == InstructorHistory.instructor_id))
        .filter(InstructorHistory.instructor_id == instructor.id)
        .all()
    )
    rows.sort(key=lambda r: (_term_key(r[0].semester), r[0].course.code, r[0].section_label), reverse=True)
    return [
        TeachingHistoryOut(
            course_code=s.course.code, course_title=s.course.title, section_label=s.section_label,
            semester=f"{s.semester.name} {s.semester.year}", feedback_score=score,
        )
        for s, score in rows
    ]


@router.get("/offered-courses", response_model=list[OfferedCourseOut])
def offered_courses(instructor: Instructor = Depends(get_faculty), db: Session = Depends(get_db)):
    """The courses my department offers this semester: what I can ask to teach."""
    semester = db.query(Semester).filter(Semester.is_active.is_(True)).first()
    if semester is None:
        return []
    rows = (
        db.query(Course.id, Course.code, Course.title, Course.credit_hours, func.count(Section.id))
        .join(Program, Course.program_id == Program.id)
        .join(Section, Section.course_id == Course.id)
        .filter(Program.department_id == instructor.department_id, Section.semester_id == semester.id)
        .group_by(Course.id, Course.code, Course.title, Course.credit_hours)
        .order_by(Course.code)
        .all()
    )
    requested = {
        p.course_id for p in
        db.query(InstructorPreference).filter_by(instructor_id=instructor.id, semester_id=semester.id)
    }
    return [
        OfferedCourseOut(course_id=cid, code=code, title=title, credit_hours=credits,
                         sections_offered=n, requested=cid in requested)
        for cid, code, title, credits, n in rows
    ]


@router.get("/preferences", response_model=list[PreferenceOut])
def my_preferences(
    semester_id: Optional[int] = Query(None, description="Defaults to the active semester"),
    instructor: Instructor = Depends(get_faculty),
    db: Session = Depends(get_db),
):
    query = db.query(InstructorPreference).filter_by(instructor_id=instructor.id)
    if semester_id is None:
        active = db.query(Semester).filter(Semester.is_active.is_(True)).first()
        if active is not None:
            query = query.filter_by(semester_id=active.id)
    else:
        query = query.filter_by(semester_id=semester_id)
    return [preference_out(p) for p in query.order_by(InstructorPreference.priority_rank).all()]


@router.post("/preferences", response_model=PreferenceOut, status_code=201)
def submit_preference(payload: PreferenceCreate, instructor: Instructor = Depends(get_faculty),
                      user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if instructor.status != "active":
        raise HTTPException(status_code=403, detail="Instructors on leave cannot submit preferences.")
    semester = _open_semester(db)

    # The course must belong to the instructor's own department...
    course = (
        db.query(Course).join(Program, Course.program_id == Program.id)
        .filter(Course.id == payload.course_id, Program.department_id == instructor.department_id)
        .first()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    # ...and actually be offered this semester.
    if db.query(Section).filter_by(course_id=course.id, semester_id=semester.id).first() is None:
        raise HTTPException(status_code=409,
                            detail=f"{course.code} is not offered in {semester.name} {semester.year}.")

    mine = db.query(InstructorPreference).filter_by(instructor_id=instructor.id, semester_id=semester.id).all()
    if any(p.course_id == course.id for p in mine):
        raise HTTPException(status_code=409, detail="You have already requested this course.")
    if len(mine) >= MAX_PREFERENCES:
        raise HTTPException(status_code=409,
                            detail=f"You can request at most {MAX_PREFERENCES} courses. Withdraw one first.")
    used = {p.priority_rank for p in mine}
    rank = payload.priority_rank
    if rank is None:
        rank = next(r for r in range(1, MAX_PREFERENCES + 1) if r not in used)
    elif rank in used:
        raise HTTPException(status_code=409,
                            detail=f"Rank {rank} is already used. Withdraw that request or pick a free rank.")

    preference = InstructorPreference(
        instructor_id=instructor.id, course_id=course.id, semester_id=semester.id,
        priority_rank=rank, approval_status="pending",
    )
    db.add(preference)
    db.flush()
    log_action(db, user, "preference_submitted", "InstructorPreference", preference.id,
               f"{instructor.name} requested {course.code} {course.title} for "
               f"{semester.name} {semester.year} as choice #{rank}")
    commit_or_409(db, "This request conflicts with an existing one.")
    db.refresh(preference)
    return preference_out(preference)


@router.delete("/preferences/{preference_id}", status_code=204)
def withdraw_preference(preference_id: int, instructor: Instructor = Depends(get_faculty),
                        user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preference = db.query(InstructorPreference).filter_by(id=preference_id, instructor_id=instructor.id).first()
    if preference is None:
        raise HTTPException(status_code=404, detail="Preference not found")
    if preference.approval_status != "pending":
        raise HTTPException(status_code=409,
                            detail=f"This request was already {preference.approval_status} and can no longer be withdrawn.")
    if preference.semester.is_locked:
        raise HTTPException(status_code=409, detail="Preferences for this semester are closed.")
    log_action(db, user, "preference_withdrawn", "InstructorPreference", preference.id,
               f"{instructor.name} withdrew {preference.course.code} "
               f"({preference.semester.name} {preference.semester.year})")
    db.delete(preference)
    db.commit()
    return Response(status_code=204)


@router.get("/allocations", response_model=list[AllocationOut])
def my_allocations(instructor: Instructor = Depends(get_faculty), db: Session = Depends(get_db)):
    """Sections a coordinator has confirmed for me. Empty until allocations are made."""
    allocations = (
        db.query(Allocation).join(Section, Allocation.section_id == Section.id)
        .filter(Allocation.instructor_id == instructor.id, Allocation.status == "confirmed")
        .all()
    )
    allocations.sort(key=lambda a: (_term_key(a.section.semester), a.section.course.code), reverse=True)
    return [
        AllocationOut(
            id=a.id, course_code=a.section.course.code, course_title=a.section.course.title,
            section_label=a.section.section_label,
            semester=f"{a.section.semester.name} {a.section.semester.year}",
            status=a.status, allocated_at=a.allocated_at,
        )
        for a in allocations
    ]


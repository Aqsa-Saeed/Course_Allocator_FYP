"""
UC-2 / UC-3: ranked, explained instructor recommendations for a section.
The section must be inside the caller's scope, otherwise it answers 404.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.access import Scope, get_scope, scoped_sections
from app.database import get_db
from app.models import Section
from app.schemas.ranking import CandidateOut, ComponentOut, ExcludedOut, RecommendationOut
from app.services.ranking import rank_instructors

router = APIRouter(prefix="/sections", tags=["recommendations"])


@router.get("/{section_id}/recommendations", response_model=RecommendationOut)
def recommendations(
    section_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    scope: Scope = Depends(get_scope),
):
    section = scoped_sections(db, scope).filter(Section.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        result = rank_instructors(db, section, limit)
    except RuntimeError as error:      # ranking settings not seeded
        raise HTTPException(status_code=503, detail=str(error))
    except ValueError as error:        # course has no embedding yet
        raise HTTPException(status_code=409, detail=str(error))

    candidates = [
        CandidateOut(
            rank=position,
            instructor_id=c.instructor.id,
            instructor_name=c.instructor.name,
            academic_rank=c.instructor.academic_rank,
            score=c.score,
            components=[
                ComponentOut(key=x.key, label=x.label, value=round(x.value, 4),
                             weight=round(x.weight, 4), contribution=round(x.contribution, 4))
                for x in c.components
            ],
            explanation=c.explanation,
        )
        for position, c in enumerate(result.candidates, start=1)
    ]
    excluded = [
        ExcludedOut(instructor_id=e.instructor.id, instructor_name=e.instructor.name, reason=e.reason)
        for e in result.excluded
    ]
    return RecommendationOut(
        section_id=section.id,
        course_code=section.course.code,
        course_title=section.course.title,
        section_label=section.section_label,
        semester=f"{section.semester.name} {section.semester.year}",
        candidates=candidates,
        excluded=excluded,
        message=None if candidates else "No eligible instructors found for this section.",
    )

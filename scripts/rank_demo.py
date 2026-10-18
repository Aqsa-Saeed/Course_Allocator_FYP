"""
Prints the ranking and explanations for sections in the semester being
allocated.

From the project root, venv active:
    python -m scripts.rank_demo                  # a few example sections
    python -m scripts.rank_demo CS-310:A AI-401:A  # specific course:section
"""

import sys

from app.database import SessionLocal
from app.models import Course, Section, Semester
from app.services.ranking import rank_instructors

DEFAULT_SECTIONS = ["AI-401:A", "CS-310:A", "CS-220:A"]


def main(args):
    db = SessionLocal()
    try:
        target = db.query(Semester).filter(Semester.is_active.is_(True)).first()
        if target is None:
            raise SystemExit("No active semester found.")
        for token in args or DEFAULT_SECTIONS:
            code, _, label = token.partition(":")
            section = (
                db.query(Section).join(Course, Section.course_id == Course.id)
                .filter(Course.code == code, Section.semester_id == target.id,
                        Section.section_label == (label or "A"))
                .first()
            )
            if section is None:
                print(f"\n{token}: no such section in {target.name} {target.year}")
                continue

            result = rank_instructors(db, section, limit=5)
            print(f"\n=== {code} {section.course.title}, section {section.section_label} "
                  f"({target.name} {target.year}) ===")
            for position, c in enumerate(result.candidates, start=1):
                bits = "  ".join(f"{x.key[:4]} {x.value:.2f}" for x in c.components)
                print(f"{position}. {c.instructor.name}  score {c.score:.3f}")
                print(f"     [{bits}]")
                print(f"     {c.explanation}")
            if result.excluded:
                print(f"  Excluded ({len(result.excluded)}): " +
                      "; ".join(f"{e.instructor.name} ({e.reason})" for e in result.excluded[:4]))
    finally:
        db.close()


if __name__ == "__main__":
    main(sys.argv[1:])

"""
See the embeddings working: prints the closest instructors for some courses,
or for any question you type.

From the project root, venv active:
    python -m scripts.embedding_demo                       # a few example courses
    python -m scripts.embedding_demo AI-401 CS-310         # specific course codes
    python -m scripts.embedding_demo "who knows computer vision"   # free text
"""

import sys

from app.database import SessionLocal
from app.models import Course
from app.services.retrieval import instructors_for_course, search_instructors

DEFAULT_COURSES = ["AI-401", "CS-310", "CS-230", "CS-220", "SE-310"]


def show(title, results):
    print(f"\n{title}")
    for instructor, similarity in results:
        print(f"  {similarity:.3f}  {instructor.name:<30} {instructor.qualifications_text}")


def main(args):
    db = SessionLocal()
    try:
        targets = args or DEFAULT_COURSES
        for target in targets:
            course = db.query(Course).filter_by(code=target).first()
            if course is not None:
                show(f"{course.code} {course.title}", instructors_for_course(db, course, limit=5))
            else:
                show(f'Search: "{target}"', search_instructors(db, target, limit=5))
    finally:
        db.close()


if __name__ == "__main__":
    main(sys.argv[1:])

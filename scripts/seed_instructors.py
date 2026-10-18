"""
Loads the Computer Science department and its faculty into the database.

Run from the project root (the folder that contains app/), venv active:
    python -m scripts.seed_instructors

Safe to run more than once. Instructors are matched by name: new ones are
added and existing ones are updated in place, so re-running never creates
duplicates (even if an earlier version of this script already loaded them).
"""

from app.database import SessionLocal
from app.models import Department, Instructor
from scripts.cs_faculty_data import DEPARTMENT_NAME, FACULTY


def main():
    db = SessionLocal()
    try:
        dept = db.query(Department).filter_by(name=DEPARTMENT_NAME).first()
        if dept is None:
            dept = Department(name=DEPARTMENT_NAME)
            db.add(dept)
            db.flush()  # assigns dept.id without committing yet

        added, updated = 0, 0
        for name, email, rank, qualification, status, specialization in FACULTY:
            instructor = db.query(Instructor).filter_by(name=name).first()
            if instructor is None:
                instructor = Instructor(name=name, department_id=dept.id)
                db.add(instructor)
                added += 1
            else:
                updated += 1

            instructor.email = email
            instructor.academic_rank = rank
            instructor.highest_qualification = qualification
            instructor.status = status
            instructor.qualifications_text = specialization

        db.commit()
        print(f"Department: {DEPARTMENT_NAME} (id={dept.id})")
        print(f"Instructors added: {added}, updated: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

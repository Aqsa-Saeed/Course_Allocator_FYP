"""
Loads the sample course catalog: programs, courses, prerequisites,
semesters and the sections offered in the semester being allocated.

Run AFTER seed_instructors (it needs the Computer Science department).
From the project root, venv active:
    python -m scripts.seed_catalog

Safe to run more than once: anything already in the database is skipped.
"""

from string import ascii_uppercase

from app.database import SessionLocal
from app.models import (
    Department, Program, Semester, Course, CoursePrerequisite, Section,
)
from scripts.cs_faculty_data import DEPARTMENT_NAME
from scripts.cs_catalog_data import (
    PROGRAMS, COURSES, PREREQUISITES, SEMESTERS,
    TARGET_SEMESTER, SECTIONS_TO_OFFER,
)


def main():
    db = SessionLocal()
    try:
        dept = db.query(Department).filter_by(name=DEPARTMENT_NAME).first()
        if dept is None:
            raise SystemExit(
                f"Department '{DEPARTMENT_NAME}' not found. "
                "Run: python -m scripts.seed_instructors first."
            )

        counts = {"programs": 0, "courses": 0, "prerequisites": 0,
                  "semesters": 0, "sections": 0}

        # Programs
        programs = {}
        for name in PROGRAMS:
            program = db.query(Program).filter_by(name=name, department_id=dept.id).first()
            if program is None:
                program = Program(name=name, department_id=dept.id)
                db.add(program)
                counts["programs"] += 1
            programs[name] = program
        db.flush()

        # Courses
        courses = {}
        for code, title, program_name, credits, requirements in COURSES:
            course = db.query(Course).filter_by(code=code).first()
            if course is None:
                course = Course(
                    code=code, title=title, credit_hours=credits,
                    program_id=programs[program_name].id,
                    requirements_text=requirements,
                )
                db.add(course)
                counts["courses"] += 1
            courses[code] = course
        db.flush()

        # Prerequisites
        for code, prereq_code in PREREQUISITES:
            exists = db.query(CoursePrerequisite).filter_by(
                course_id=courses[code].id,
                prerequisite_course_id=courses[prereq_code].id,
            ).first()
            if exists is None:
                db.add(CoursePrerequisite(
                    course_id=courses[code].id,
                    prerequisite_course_id=courses[prereq_code].id,
                ))
                counts["prerequisites"] += 1

        # Semesters
        semesters = {}
        for name, year, is_active, is_locked in SEMESTERS:
            semester = db.query(Semester).filter_by(name=name, year=year).first()
            if semester is None:
                semester = Semester(name=name, year=year,
                                    is_active=is_active, is_locked=is_locked)
                db.add(semester)
                counts["semesters"] += 1
            semesters[(name, year)] = semester
        db.flush()

        # Sections offered in the semester being allocated
        target = semesters[TARGET_SEMESTER]
        for code, how_many in SECTIONS_TO_OFFER.items():
            for label in ascii_uppercase[:how_many]:
                exists = db.query(Section).filter_by(
                    course_id=courses[code].id,
                    semester_id=target.id,
                    section_label=label,
                ).first()
                if exists is None:
                    db.add(Section(course_id=courses[code].id,
                                   semester_id=target.id,
                                   section_label=label))
                    counts["sections"] += 1

        db.commit()
        print("Added:", ", ".join(f"{v} {k}" for k, v in counts.items()))
    finally:
        db.close()


if __name__ == "__main__":
    main()

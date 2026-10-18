"""
Generates SYNTHETIC instructor preferences for the semester being allocated
(the active semester): which courses each instructor asked to teach, in
priority order, and whether the coordinator has reviewed them yet.

Run AFTER seed_instructors and seed_catalog (and ideally seed_history, which
makes instructors favour courses they have taught before). From the project
root, venv active:
    python -m scripts.seed_preferences            # generate (skips if they exist)
    python -m scripts.seed_preferences --reset    # replace this semester's preferences

Deterministic (fixed SEED), so regenerating gives the same result. The rules:

  1. Not everyone submits. Each active instructor submits with probability
     SUBMIT_CHANCE; instructors on leave never do.
  2. Each submitter ranks 1 to 3 courses (rank 1 = first choice).
  3. Choices follow specialization and history. A course is more likely to be
     picked if it matches the instructor's specialization or they have
     taught it before; a small baseline lets people occasionally ask for
     something outside their field.
  4. Review status is mixed on purpose, so the approval workflow has
     something to show. Requests outside an instructor's specialty are far
     more likely to be rejected.
"""

import argparse
import random
from collections import Counter

from app.database import SessionLocal
from app.models import (
    Instructor, Course, Semester, Section,
    InstructorHistory, InstructorPreference,
)
from scripts.seed_history import affinity

# --- Tunable knobs -----------------------------------------------------------
SEED = 2027
SUBMIT_CHANCE = 0.75
CHOICES_COUNT = [1, 2, 3]
CHOICES_WEIGHTS = [0.25, 0.45, 0.30]
HISTORY_WEIGHT = 2.0       # extra pull per time the instructor taught the course
BASELINE_WEIGHT = 0.05     # keeps out-of-field requests possible but rare
STATUSES = ["approved", "pending", "rejected"]
STATUS_IN_FIELD = (0.45, 0.50, 0.05)
STATUS_OUT_OF_FIELD = (0.20, 0.30, 0.50)
# -----------------------------------------------------------------------------


def main(reset=False):
    db = SessionLocal()
    try:
        target = db.query(Semester).filter(Semester.is_active.is_(True)).first()
        if target is None:
            raise SystemExit("No active semester found. Run seed_catalog first.")

        existing = db.query(InstructorPreference).filter_by(semester_id=target.id)
        if reset:
            existing.delete()
            db.flush()
            print(f"Cleared existing preferences for {target.name} {target.year}.")
        elif existing.first() is not None:
            print("Preferences already exist for this semester, nothing to do. "
                  "Use --reset to regenerate.")
            return

        instructors = db.query(Instructor).order_by(Instructor.id).all()
        courses = db.query(Course).order_by(Course.code).all()
        if not instructors or not courses:
            raise SystemExit("Run seed_instructors and seed_catalog first.")

        # How many times each instructor has taught each course
        taught = Counter()
        rows = (db.query(InstructorHistory.instructor_id, Section.course_id)
                .join(Section, InstructorHistory.section_id == Section.id).all())
        for instructor_id, course_id in rows:
            taught[(instructor_id, course_id)] += 1

        rng = random.Random(SEED)
        submitters = 0
        status_counts = Counter()
        requested = Counter()
        in_field = 0
        total = 0

        for instructor in instructors:
            if instructor.status != "active":
                continue
            if rng.random() > SUBMIT_CHANCE:
                continue
            submitters += 1

            terms = [t.strip() for t in (instructor.qualifications_text or "").split(",")
                     if t.strip()]
            remaining = list(courses)
            how_many = rng.choices(CHOICES_COUNT, CHOICES_WEIGHTS)[0]

            for rank in range(1, how_many + 1):
                fits = [affinity(terms, c) for c in remaining]
                weights = [
                    fit * fit + HISTORY_WEIGHT * taught[(instructor.id, c.id)] + BASELINE_WEIGHT
                    for fit, c in zip(fits, remaining)
                ]
                index = rng.choices(range(len(remaining)), weights)[0]
                course, fit = remaining.pop(index), fits[index]

                probabilities = STATUS_IN_FIELD if fit > 0 else STATUS_OUT_OF_FIELD
                status = rng.choices(STATUSES, probabilities)[0]

                db.add(InstructorPreference(
                    instructor_id=instructor.id, course_id=course.id,
                    semester_id=target.id, priority_rank=rank,
                    approval_status=status,
                ))
                status_counts[status] += 1
                requested[course.code] += 1
                total += 1
                if fit > 0:
                    in_field += 1

        db.commit()

        print(f"Semester: {target.name} {target.year}")
        print(f"Instructors who submitted: {submitters}, preference rows: {total}")
        print("Review status: " + ", ".join(f"{k} {status_counts[k]}" for k in STATUSES))
        print(f"Requests inside the instructor's specialty: {in_field / total:.0%}")
        top = ", ".join(f"{code} ({n})" for code, n in requested.most_common(5))
        print(f"Most requested: {top}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--reset", action="store_true",
                        help="delete this semester's preferences and regenerate")
    main(reset=parser.parse_args().reset)

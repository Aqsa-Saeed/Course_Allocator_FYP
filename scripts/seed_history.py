"""
Generates SYNTHETIC teaching history for the sample catalog: who taught which
section in past semesters, the feedback scores they received, and each
instructor's workload per semester.

Run AFTER seed_instructors and seed_catalog, from the project root, venv active:
    python -m scripts.seed_history            # generate (skips if history exists)
    python -m scripts.seed_history --reset    # wipe history/feedback/workload and regenerate

The data is random but deterministic (fixed SEED), so regenerating gives the
same result. The rules below are what make it look like a real department
rather than noise, and they are the first thing to change if you want
different behaviour.

  1. Specialization drives assignment. An instructor is much more likely to
     teach a course whose requirements match their specialization.
  2. Instructors repeat courses. Each semester, a section is usually taught
     by the same person as last semester (STICKINESS), which creates the
     "taught this course 2 of the last 3 semesters" patterns the ranking uses.
  3. Nobody is overloaded. No instructor teaches more than
     MAX_SECTIONS_PER_TERM sections in one semester.
  4. Feedback reflects the instructor plus fit. Each instructor has a base
     quality; teaching inside their specialty nudges the score up, outside
     it nudges it down, plus some random noise.
  5. The semester in progress has history but no feedback yet, because
     feedback is collected at the end of a semester.
"""

import argparse
import random
import re
from collections import Counter, defaultdict
from string import ascii_uppercase

from app.database import SessionLocal
from app.models import (
    Instructor, Course, Section, Semester,
    InstructorHistory, FeedbackScore, Workload,
)
from scripts.cs_catalog_data import SECTIONS_TO_OFFER

# --- Tunable knobs -----------------------------------------------------------
SEED = 2026
STICKINESS = 0.6               # chance a section keeps last semester's instructor
OUT_OF_FIELD_CHANCE = 0.05     # chance a section goes to a random available instructor
MAX_SECTIONS_PER_TERM = 4
CURRENT_SEMESTER = ("Fall", 2026)        # in progress: no feedback collected yet
ON_LEAVE_LAST_SEMESTER = ("Fall", 2025)  # instructors now on leave taught only up to here
GENERALIST_TERMS = {"computer science", "programming subjects"}
GENERALIST_BONUS = 0.5         # generalists get a weak match to every core CS course
STOPWORDS = {"and", "of", "the", "for"}
# -----------------------------------------------------------------------------


def term_key(name, year):
    """Sort key so Spring comes before Fall within a year."""
    return (year, 0 if name == "Spring" else 1)


def words(text):
    text = re.sub(r"\(.*?\)", " ", text.lower())
    return {w for w in re.findall(r"[a-z]+", text) if w not in STOPWORDS}


def affinity(terms, course):
    """
    How well an instructor's specializations match a course: one point for
    each specialization whose words all appear in the course requirements,
    plus a small bonus for generalists on core CS courses.
    """
    course_words = words(course.requirements_text or "")
    specialist = [t for t in terms if t.lower() not in GENERALIST_TERMS]
    score = sum(1 for t in specialist if words(t) and words(t) <= course_words)
    if len(specialist) < len(terms) and course.code.startswith("CS-"):
        score += GENERALIST_BONUS
    return score


def main(reset=False):
    db = SessionLocal()
    try:
        if reset:
            db.query(FeedbackScore).delete()
            db.query(InstructorHistory).delete()
            db.query(Workload).delete()
            db.flush()
            print("Cleared existing history, feedback and workload.")
        elif db.query(InstructorHistory).first() is not None:
            print("Teaching history already exists, nothing to do. "
                  "Use --reset to regenerate.")
            return

        instructors = db.query(Instructor).order_by(Instructor.id).all()
        courses = db.query(Course).order_by(Course.code).all()
        if not instructors or not courses:
            raise SystemExit("Run seed_instructors and seed_catalog first.")
        course_by_id = {c.id: c for c in courses}
        course_by_code = {c.code: c for c in courses}
        by_id = {i.id: i for i in instructors}

        # Every semester except the one being allocated, oldest first
        semesters = db.query(Semester).filter(Semester.is_active.is_(False)).all()
        semesters.sort(key=lambda s: term_key(s.name, s.year))
        if not semesters:
            raise SystemExit("No past semesters found. Run seed_catalog first.")

        # Create the sections offered in each past semester
        for sem in semesters:
            for code, how_many in SECTIONS_TO_OFFER.items():
                for label in ascii_uppercase[:how_many]:
                    exists = db.query(Section).filter_by(
                        course_id=course_by_code[code].id,
                        semester_id=sem.id,
                        section_label=label,
                    ).first()
                    if exists is None:
                        db.add(Section(course_id=course_by_code[code].id,
                                       semester_id=sem.id,
                                       section_label=label))
        db.flush()

        sections_by_sem = {}
        for sem in semesters:
            secs = db.query(Section).filter_by(semester_id=sem.id).all()
            secs.sort(key=lambda s: (course_by_id[s.course_id].code, s.section_label))
            sections_by_sem[sem.id] = secs

        # Precompute how well each instructor fits each course
        terms = {
            i.id: [t.strip() for t in (i.qualifications_text or "").split(",") if t.strip()]
            for i in instructors
        }
        aff = {(i.id, c.code): affinity(terms[i.id], c)
               for i in instructors for c in courses}

        rng = random.Random(SEED)
        quality = {i.id: min(4.9, max(2.8, rng.gauss(3.9, 0.45))) for i in instructors}

        last_taught_by = {}   # (course code, section label) -> instructor id, previous semester
        history_rows = 0
        feedback_rows = 0
        workload_rows = 0
        in_field = 0
        feedback_scores = []
        busiest = 0
        per_semester = []

        for sem in semesters:
            sem_label = (sem.name, sem.year)
            load = Counter()
            credits = Counter()
            taught_now = {}

            for section in sections_by_sem[sem.id]:
                course = course_by_id[section.course_id]
                available = [
                    i for i in instructors
                    if load[i.id] < MAX_SECTIONS_PER_TERM
                    and (i.status == "active"
                         or term_key(*sem_label) <= term_key(*ON_LEAVE_LAST_SEMESTER))
                ]
                available_ids = {i.id for i in available}

                chosen = None
                previous_id = last_taught_by.get((course.code, section.section_label))
                if previous_id in available_ids and rng.random() < STICKINESS:
                    chosen = by_id[previous_id]

                if chosen is None:
                    if rng.random() < OUT_OF_FIELD_CHANCE:
                        chosen = rng.choice(available)
                    else:
                        pool = [(i, aff[(i.id, course.code)]) for i in available
                                if aff[(i.id, course.code)] > 0]
                        if pool:
                            chosen = rng.choices(
                                [i for i, _ in pool],
                                weights=[a * a for _, a in pool],
                            )[0]
                        else:
                            chosen = rng.choice(available)

                fit = aff[(chosen.id, course.code)]
                load[chosen.id] += 1
                credits[chosen.id] += course.credit_hours
                taught_now[(course.code, section.section_label)] = chosen.id
                db.add(InstructorHistory(instructor_id=chosen.id, section_id=section.id))
                history_rows += 1
                if fit > 0:
                    in_field += 1

                if sem_label != CURRENT_SEMESTER:
                    nudge = 0.15 if fit >= 2 else 0.05 if fit >= 1 else 0.0 if fit > 0 else -0.25
                    score = quality[chosen.id] + nudge + rng.gauss(0, 0.25)
                    score = round(min(5.0, max(2.0, score)), 2)
                    db.add(FeedbackScore(instructor_id=chosen.id,
                                         section_id=section.id, score=score))
                    feedback_rows += 1
                    feedback_scores.append(score)

            for instructor_id, count in load.items():
                db.add(Workload(instructor_id=instructor_id, semester_id=sem.id,
                                course_count=count,
                                total_credit_hours=credits[instructor_id]))
                workload_rows += 1
            busiest = max(busiest, max(load.values()))
            per_semester.append((sem_label, len(sections_by_sem[sem.id]), len(load)))
            last_taught_by = taught_now

        db.commit()

        print(f"Semesters filled: {', '.join(f'{n} {y}' for (n, y), _, _ in per_semester)}")
        print(f"History rows: {history_rows}, feedback rows: {feedback_rows}, "
              f"workload rows: {workload_rows}")
        print(f"Assignments inside the instructor's specialty: "
              f"{in_field / history_rows:.0%}")
        print(f"Feedback: mean {sum(feedback_scores) / len(feedback_scores):.2f}, "
              f"min {min(feedback_scores):.2f}, max {max(feedback_scores):.2f}")
        print(f"Most sections taught by one instructor in a semester: {busiest}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--reset", action="store_true",
                        help="delete existing history/feedback/workload and regenerate")
    main(reset=parser.parse_args().reset)

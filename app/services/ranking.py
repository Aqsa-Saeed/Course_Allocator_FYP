"""
Ranking engine: for one section, score every instructor and explain why.

Each instructor gets six signals, each scaled to 0..1:

    expertise    embedding similarity between their specializations and the course
    history      semesters they taught THIS course (related courses count half)
    recency      how recently they last taught this course
    feedback     their average rating, smoothed toward the department average
    preference   whether they asked for this course (rank and review status matter)
    workload     fewer sections already confirmed this semester -> higher

The final score is the weighted average of those signals, using the weights in
the ranking_settings table. Policy rules are NOT weighed: an instructor who is
on leave, at the workload cap, or below the minimum feedback score is excluded
and listed separately with the reason, so the coordinator can see who was
filtered out and why.

Only information from semesters BEFORE the section's semester is used.
"""

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Allocation, CoursePrerequisite, FeedbackScore, Instructor,
    InstructorHistory, InstructorPreference, RankingSettings, Section, Semester,
)

# --- Tunable constants -------------------------------------------------------
SMOOTHING_STRENGTH = 3        # pretend every instructor already has this many average ratings
FALLBACK_PRIOR = 3.5          # department average to use if no feedback exists anywhere yet
HISTORY_FULL_CREDIT = 3       # semesters of experience that earn a perfect history score
RELATED_WEIGHT = 0.5          # a related course offering counts this much of an exact one
RECENCY_STEP = 0.25           # recency drops by this much per semester since last teaching it
PREFERENCE_BY_RANK = {1: 1.0, 2: 0.75, 3: 0.5}
PREFERENCE_OTHER_RANK = 0.4
PREFERENCE_STATUS_FACTOR = {"approved": 1.0, "pending": 0.6, "rejected": 0.0}
# -----------------------------------------------------------------------------

LABELS = {
    "expertise": "Expertise match",
    "history": "Teaching history",
    "recency": "Recent teaching",
    "feedback": "Student feedback",
    "preference": "Instructor preference",
    "workload": "Workload balance",
}


@dataclass
class Component:
    key: str
    label: str
    value: float          # 0..1
    weight: float         # normalized, all weights sum to 1

    @property
    def contribution(self) -> float:
        return self.value * self.weight


@dataclass
class Candidate:
    instructor: Instructor
    score: float
    components: list
    explanation: str


@dataclass
class Excluded:
    instructor: Instructor
    reason: str


@dataclass
class RankingResult:
    section: Section
    candidates: list
    excluded: list


def term_key(semester) -> tuple:
    """Chronological sort key: Spring comes before Fall within a year."""
    return (semester.year, 0 if semester.name == "Spring" else 1)


def smooth(total: float, count: int, prior: float, strength: int = SMOOTHING_STRENGTH) -> float:
    """
    Bayesian-style smoothing: blend the instructor's own ratings with the
    department average. With few ratings the result stays near the average;
    with many it converges to the instructor's own mean.
    """
    return (total + strength * prior) / (count + strength)


def preference_value(preference) -> float:
    if preference is None:
        return 0.0
    base = PREFERENCE_BY_RANK.get(preference.priority_rank, PREFERENCE_OTHER_RANK)
    return base * PREFERENCE_STATUS_FACTOR.get(preference.approval_status, 0.0)


def _ordinal(n: int) -> str:
    return {1: "first", 2: "second", 3: "third"}.get(n, f"#{n}")


def get_settings(db: Session) -> RankingSettings:
    settings = db.query(RankingSettings).first()
    if settings is None:
        raise RuntimeError("No ranking settings found. Run: python -m scripts.seed_ranking_settings")
    return settings


def past_semesters(db: Session, target) -> list:
    """Semesters strictly before `target`, oldest first."""
    return sorted((s for s in db.query(Semester).all() if term_key(s) < term_key(target)), key=term_key)


def feedback_stats(db: Session, past_ids: list):
    """
    Each instructor's feedback total and count over past semesters, plus the
    department-wide average, which is the "prior" that smoothing pulls toward.
    """
    total, count, all_scores = defaultdict(float), defaultdict(int), []
    for instructor_id, score in (
        db.query(FeedbackScore.instructor_id, FeedbackScore.score)
        .join(Section, FeedbackScore.section_id == Section.id)
        .filter(Section.semester_id.in_(past_ids))
        .all()
    ):
        total[instructor_id] += score
        count[instructor_id] += 1
        all_scores.append(score)
    return total, count, (mean(all_scores) if all_scores else FALLBACK_PRIOR)


def confirmed_load(db: Session, semester_id: int) -> dict:
    """Sections each instructor already has confirmed in this semester."""
    return dict(
        db.query(Allocation.instructor_id, func.count(Allocation.id))
        .join(Section, Allocation.section_id == Section.id)
        .filter(Section.semester_id == semester_id, Allocation.status == "confirmed")
        .group_by(Allocation.instructor_id)
        .all()
    )


def violations(instructor, smoothed: float, current_load: int, settings) -> list:
    """
    The policy rules this instructor breaks, as (code, message) pairs.
    An empty list means they are eligible. ALL broken rules are reported,
    not just the first, so a coordinator sees everything to fix at once.
    """
    problems = []
    if instructor.status != "active":
        problems.append(("on_leave", "On leave"))
    if current_load >= settings.max_courses_per_instructor:
        problems.append((
            "workload_cap",
            f"Already at the workload cap ({current_load} of {settings.max_courses_per_instructor} sections)",
        ))
    if smoothed < settings.min_feedback_score:
        problems.append((
            "low_feedback",
            f"Feedback score {smoothed:.1f}/5 is below the minimum of {settings.min_feedback_score:g}",
        ))
    return problems


def policy_violations(db: Session, section: Section, instructor: Instructor) -> list:
    """The same policy check the ranking uses, for one instructor and one section."""
    settings = get_settings(db)
    past_ids = [s.id for s in past_semesters(db, section.semester)]
    total, count, prior = feedback_stats(db, past_ids)
    smoothed = smooth(total[instructor.id], count[instructor.id], prior)
    current_load = confirmed_load(db, section.semester_id).get(instructor.id, 0)
    return violations(instructor, smoothed, current_load, settings)


def rank_instructors(db: Session, section: Section, limit: int = 10) -> RankingResult:
    settings = get_settings(db)

    course = section.course
    target = section.semester
    if course.requirements_embedding is None:
        raise ValueError(f"{course.code} has no embedding yet. Run: python -m scripts.generate_embeddings")

    # Weights, normalized so they always sum to 1 even if an admin edits them oddly
    raw_weights = {
        "expertise": settings.weight_content_match,
        "history": settings.weight_history,
        "recency": settings.weight_recency,
        "feedback": settings.weight_feedback,
        "preference": settings.weight_preference,
        "workload": settings.weight_workload,
    }
    total_weight = sum(raw_weights.values()) or 1.0
    weights = {k: v / total_weight for k, v in raw_weights.items()}

    # Semesters strictly before the target, oldest first
    past = past_semesters(db, target)
    past_ids = [s.id for s in past]
    index_of = {s.id: i for i, s in enumerate(past)}
    semester_by_id = {s.id: s for s in past}

    # Courses whose teaching counts as related experience: direct prerequisites and dependents
    prereq_ids = {r.prerequisite_course_id for r in db.query(CoursePrerequisite).filter_by(course_id=course.id)}
    dependent_ids = {r.course_id for r in db.query(CoursePrerequisite).filter_by(prerequisite_course_id=course.id)}
    related_ids = prereq_ids | dependent_ids

    exact_semesters = defaultdict(set)   # instructor id -> semesters they taught this course
    related_offerings = defaultdict(set)  # instructor id -> (related course, semester) pairs
    rows = (
        db.query(InstructorHistory.instructor_id, Section.course_id, Section.semester_id)
        .join(Section, InstructorHistory.section_id == Section.id)
        .filter(Section.semester_id.in_(past_ids), Section.course_id.in_({course.id} | related_ids))
        .all()
    )
    for instructor_id, course_id, semester_id in rows:
        if course_id == course.id:
            exact_semesters[instructor_id].add(semester_id)
        else:
            related_offerings[instructor_id].add((course_id, semester_id))

    feedback_total, feedback_count, prior = feedback_stats(db, past_ids)

    # Embedding similarity, computed inside PostgreSQL by pgvector
    distance = Instructor.qualifications_embedding.cosine_distance(course.requirements_embedding)
    similarity = {
        instructor_id: max(0.0, 1.0 - float(d))
        for instructor_id, d in db.query(Instructor.id, distance)
        .filter(Instructor.qualifications_embedding.isnot(None)).all()
    }

    preferences = {
        p.instructor_id: p
        for p in db.query(InstructorPreference).filter_by(course_id=course.id, semester_id=target.id)
    }

    load = confirmed_load(db, target.id)

    max_load = settings.max_courses_per_instructor
    candidates, excluded = [], []

    for instructor in db.query(Instructor).order_by(Instructor.id).all():
        n_ratings = feedback_count[instructor.id]
        smoothed = smooth(feedback_total[instructor.id], n_ratings, prior)
        current_load = load.get(instructor.id, 0)

        # --- Policy checks (hard filters) ---
        problems = violations(instructor, smoothed, current_load, settings)
        if problems:
            excluded.append(Excluded(instructor, "; ".join(message for _, message in problems)))
            continue

        # --- Signals, each 0..1 ---
        n_exact = len(exact_semesters[instructor.id])
        n_related = len(related_offerings[instructor.id])
        history = min(1.0, (n_exact + RELATED_WEIGHT * n_related) / HISTORY_FULL_CREDIT)

        if n_exact:
            last_id = max(exact_semesters[instructor.id], key=lambda sid: index_of[sid])
            semesters_ago = len(past) - 1 - index_of[last_id]
            recency = max(0.0, 1.0 - RECENCY_STEP * semesters_ago)
            last_label = f"{semester_by_id[last_id].name} {semester_by_id[last_id].year}"
        else:
            recency, last_label = 0.0, None

        preference = preferences.get(instructor.id)
        values = {
            "expertise": min(1.0, similarity.get(instructor.id, 0.0)),
            "history": history,
            "recency": recency,
            "feedback": max(0.0, min(1.0, smoothed / 5.0)),
            "preference": preference_value(preference),
            "workload": max(0.0, 1.0 - current_load / max_load),
        }
        components = [Component(k, LABELS[k], values[k], weights[k]) for k in LABELS]
        score = sum(c.contribution for c in components)

        # --- Explanation, built from the same numbers ---
        parts = []
        if n_exact:
            parts.append(f"taught {course.title} in {n_exact} of the last {len(past)} semesters "
                         f"(most recently {last_label})")
        elif n_related:
            parts.append(f"has not taught {course.title} but has related teaching experience "
                         f"({n_related} related course offering{'s' if n_related != 1 else ''})")
        else:
            parts.append(f"has no prior teaching history for {course.title}")
        parts.append(f"specialization match {values['expertise']:.2f} ({instructor.qualifications_text})")
        if n_ratings:
            parts.append(f"feedback {smoothed:.1f}/5 across {n_ratings} rated section{'s' if n_ratings != 1 else ''}")
        else:
            parts.append("no feedback on record yet, so scored at the department average")
        if preference is None:
            parts.append("did not request this course")
        else:
            parts.append(f"requested this course as a {_ordinal(preference.priority_rank)} choice "
                         f"({preference.approval_status})")
        parts.append(f"currently {current_load} of {max_load} sections this semester")
        explanation = parts[0][0].upper() + "; ".join(parts)[1:] + "."

        candidates.append(Candidate(instructor, round(score, 4), components, explanation))

    candidates.sort(key=lambda c: (-c.score, c.instructor.name))
    excluded.sort(key=lambda e: e.instructor.name)
    return RankingResult(section, candidates[:limit], excluded)

"""
Semantic retrieval: find the instructors or courses whose embeddings are
closest to a given course, instructor, or free-text question.

This is the "R" in RAG. pgvector does the nearest-neighbour search inside
PostgreSQL using cosine distance (the <=> operator). Distance is 0 for
identical meaning, so we report similarity = 1 - distance (higher is closer).
"""

from sqlalchemy.orm import Session

from app.models import Course, Instructor
from app.services.embeddings import embed_text


def similar_instructors(db: Session, query_vector, limit: int = 10, only_active: bool = True):
    """Instructors whose specializations are closest to `query_vector`."""
    distance = Instructor.qualifications_embedding.cosine_distance(query_vector)
    query = (
        db.query(Instructor, distance.label("distance"))
        .filter(Instructor.qualifications_embedding.isnot(None))
    )
    if only_active:
        query = query.filter(Instructor.status == "active")
    rows = query.order_by(distance).limit(limit).all()
    return [(instructor, 1.0 - float(d)) for instructor, d in rows]


def similar_courses(db: Session, query_vector, limit: int = 10):
    """Courses whose requirements are closest to `query_vector`."""
    distance = Course.requirements_embedding.cosine_distance(query_vector)
    rows = (
        db.query(Course, distance.label("distance"))
        .filter(Course.requirements_embedding.isnot(None))
        .order_by(distance)
        .limit(limit)
        .all()
    )
    return [(course, 1.0 - float(d)) for course, d in rows]


def instructors_for_course(db: Session, course: Course, limit: int = 10, only_active: bool = True):
    """Which instructors best match this course's requirements?"""
    if course.requirements_embedding is None:
        raise ValueError(f"{course.code} has no embedding yet. Run generate_embeddings first.")
    return similar_instructors(db, course.requirements_embedding, limit, only_active)


def courses_for_instructor(db: Session, instructor: Instructor, limit: int = 10):
    """Which courses best match this instructor's specializations?"""
    if instructor.qualifications_embedding is None:
        raise ValueError(f"{instructor.name} has no embedding yet. Run generate_embeddings first.")
    return similar_courses(db, instructor.qualifications_embedding, limit)


def search_instructors(db: Session, text: str, limit: int = 10, only_active: bool = True):
    """Free-text search, e.g. 'who knows about computer vision?'. Used by the chat later."""
    return similar_instructors(db, embed_text(text), limit, only_active)

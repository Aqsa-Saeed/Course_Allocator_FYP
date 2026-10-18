"""
Generates embeddings for every instructor and course and stores them in the
pgvector columns.

Run after the seed scripts, from the project root, venv active:
    python -m scripts.generate_embeddings            # only rows that have no embedding yet
    python -m scripts.generate_embeddings --force    # redo everything (after editing the text)

The first run downloads the embedding model (~90 MB) and needs internet.
"""

import argparse

from app.database import SessionLocal
from app.models import Course, Instructor
from app.services.embeddings import (
    MODEL_NAME, course_text, embed_texts, instructor_text,
)


def embed_rows(rows, text_of, column):
    """Embed the given rows in one batch and write the vectors onto them."""
    pairs = [(row, text_of(row)) for row in rows]
    pairs = [(row, text) for row, text in pairs if text]   # nothing to embed -> skip
    if not pairs:
        return 0
    vectors = embed_texts([text for _, text in pairs])
    for (row, _), vector in zip(pairs, vectors):
        setattr(row, column, vector)
    return len(pairs)


def main(force=False):
    db = SessionLocal()
    try:
        instructors = db.query(Instructor).order_by(Instructor.id)
        courses = db.query(Course).order_by(Course.code)
        if not force:
            instructors = instructors.filter(Instructor.qualifications_embedding.is_(None))
            courses = courses.filter(Course.requirements_embedding.is_(None))

        print(f"Model: {MODEL_NAME}")
        n_instructors = embed_rows(instructors.all(), instructor_text, "qualifications_embedding")
        n_courses = embed_rows(courses.all(), course_text, "requirements_embedding")
        db.commit()
        print(f"Embedded {n_instructors} instructors and {n_courses} courses.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--force", action="store_true",
                        help="re-embed everything, even rows that already have a vector")
    main(force=parser.parse_args().force)

"""Vector retrieval over rag_chunks (pgvector cosine distance) with metadata filters."""
import re
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .config import settings
from .embeddings import embed_query
from .models import RagChunk, RagDocument


@dataclass
class Hit:
    chunk_id: int
    document_id: int
    title: str
    filename: str
    doc_type: str
    page: int | None
    course_code: str | None
    instructor_name: str | None
    semester: str | None
    score: float
    text: str


_HONORIFICS = re.compile(r"\b(dr|prof|professor|mr|mrs|ms|sir|madam|engr)\.?\s+", re.I)


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def detect_entities(db: Session, message: str, department_id: int) -> dict:
    """Spot instructor names / course codes mentioned in the question so that
    'What do students say about Dr. Khan?' is automatically scoped to Khan's documents."""
    rows = db.execute(
        select(RagDocument.instructor_name, RagDocument.course_code)
        .where(RagDocument.department_id == department_id)
        .distinct()
    ).all()
    msg_lower = message.lower()
    msg_alnum = _alnum(message)

    instructors, courses = set(), set()
    for name, code in rows:
        if name:
            clean = _HONORIFICS.sub("", name).strip().lower()
            parts = [p for p in re.split(r"\s+", clean) if len(p) >= 4]
            if clean and (clean in msg_lower or any(re.search(rf"\b{re.escape(p)}\b", msg_lower) for p in parts)):
                instructors.add(name)
        if code and len(_alnum(code)) >= 3 and _alnum(code) in msg_alnum:
            courses.add(code)
    return {"instructors": sorted(instructors), "courses": sorted(courses)}


def build_search_query(message: str, history: list[dict]) -> str:
    """Short follow-ups ('and what about the grading?') borrow context from the last user turn."""
    if history and len(message.split()) < 8:
        prev = next((h["content"] for h in reversed(history) if h["role"] == "user"), "")
        if prev:
            return f"{prev}\n{message}"
    return message


def retrieve(
    db: Session,
    query: str,
    *,
    department_id: int,
    top_k: int | None = None,
    doc_type: str | None = None,
    instructor_id: int | None = None,
    course_code: str | None = None,
    document_ids: list[int] | None = None,
    auto_instructors: list[str] | None = None,
    auto_courses: list[str] | None = None,
) -> list[Hit]:
    top_k = top_k or settings.top_k
    qvec = embed_query(query)
    distance = RagChunk.embedding.cosine_distance(qvec).label("distance")

    def run(use_auto: bool) -> list[Hit]:
        stmt = (
            select(RagChunk, RagDocument, distance)
            .join(RagDocument, RagChunk.document_id == RagDocument.id)
            .where(RagDocument.department_id == department_id)
        )
        if doc_type:
            stmt = stmt.where(RagDocument.doc_type == doc_type)
        if instructor_id is not None:
            stmt = stmt.where(RagDocument.instructor_id == instructor_id)
        if course_code:
            stmt = stmt.where(RagDocument.course_code == course_code)
        if document_ids:
            stmt = stmt.where(RagDocument.id.in_(document_ids))
        if use_auto and (auto_instructors or auto_courses):
            conds = []
            if auto_instructors:
                conds.append(RagDocument.instructor_name.in_(auto_instructors))
            if auto_courses:
                conds.append(RagDocument.course_code.in_(auto_courses))
            stmt = stmt.where(or_(*conds))
        stmt = stmt.order_by(distance).limit(top_k * 4)

        hits: list[Hit] = []
        per_doc: dict[int, int] = {}
        for chunk, doc, dist in db.execute(stmt).all():
            score = 1.0 - float(dist)
            if score < settings.min_score:
                continue
            if per_doc.get(doc.id, 0) >= settings.max_chunks_per_doc:
                continue  # keep results diverse across documents
            per_doc[doc.id] = per_doc.get(doc.id, 0) + 1
            hits.append(
                Hit(
                    chunk_id=chunk.id, document_id=doc.id, title=doc.title,
                    filename=doc.filename, doc_type=doc.doc_type, page=chunk.page_number,
                    course_code=doc.course_code, instructor_name=doc.instructor_name,
                    semester=doc.semester, score=round(score, 4), text=chunk.content,
                )
            )
            if len(hits) >= top_k:
                break
        return hits

    hits = run(use_auto=True)
    if not hits and (auto_instructors or auto_courses):
        hits = run(use_auto=False)  # auto-scoping found nothing: widen rather than fail
    return hits

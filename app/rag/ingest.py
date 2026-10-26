"""Upload pipeline: validate -> save -> extract -> chunk -> embed -> store."""
import hashlib
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .chunking import chunk_document
from .config import ALLOWED_EXTENSIONS, DOC_TYPES, settings
from .embeddings import embed_documents
from .extract import ExtractionError, extract_text
from .models import RagChunk, RagDocument

MAX_CHUNKS = 3000


class IngestError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _safe_name(name: str) -> str:
    name = Path(name).name
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:150] or "document"


def ingest(
    db: Session,
    *,
    department_id: int,
    data: bytes,
    filename: str,
    doc_type: str,
    title: str | None = None,
    course_id: int | None = None,
    course_code: str | None = None,
    instructor_id: int | None = None,
    instructor_name: str | None = None,
    semester: str | None = None,
) -> RagDocument:
    if doc_type not in DOC_TYPES:
        raise IngestError(f"doc_type must be one of: {', '.join(sorted(DOC_TYPES))}")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise IngestError(f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}", 415)
    if not data:
        raise IngestError("The uploaded file is empty.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise IngestError(f"File is larger than {settings.max_upload_mb} MB.", 413)
    if doc_type == "faculty_feedback" and not (instructor_id or (instructor_name or "").strip()):
        raise IngestError("Faculty feedback needs a faculty member: provide instructor_name (or instructor_id).")

    digest = hashlib.sha256(data).hexdigest()
    existing = db.scalar(
        select(RagDocument).where(
            RagDocument.department_id == department_id,
            RagDocument.content_hash == digest,
            RagDocument.doc_type == doc_type,
        )
    )
    if existing:
        raise IngestError(f"This file was already uploaded as '{existing.title}' (id {existing.id}).", 409)

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    # department in the name so two departments uploading the same file never share (or delete) one file
    stored = settings.upload_dir / f"d{department_id}_{digest[:12]}_{_safe_name(filename)}"
    stored.write_bytes(data)

    try:
        try:
            segments = extract_text(stored)
        except ExtractionError as e:
            raise IngestError(str(e), 422)

        chunks = chunk_document(segments, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise IngestError("No usable text found in the document.", 422)
        if len(chunks) > MAX_CHUNKS:
            raise IngestError(f"Document is too large ({len(chunks)} chunks; limit {MAX_CHUNKS}).", 413)

        vectors = embed_documents([c for _, c in chunks])

        pages = {p for p, _ in segments if p}
        doc = RagDocument(
            department_id=department_id,
            title=(title or "").strip() or Path(filename).stem,
            filename=_safe_name(filename),
            stored_path=str(stored),
            content_hash=digest,
            doc_type=doc_type,
            course_id=course_id,
            course_code=(course_code or "").strip().upper() or None,
            instructor_id=instructor_id,
            instructor_name=(instructor_name or "").strip() or None,
            semester=(semester or "").strip() or None,
            num_pages=len(pages),
            num_chunks=len(chunks),
        )
        db.add(doc)
        db.flush()
        db.add_all(
            RagChunk(document_id=doc.id, chunk_index=i, page_number=page, content=text, embedding=vec)
            for i, ((page, text), vec) in enumerate(zip(chunks, vectors))
        )
        db.commit()
        return doc
    except Exception:
        db.rollback()
        stored.unlink(missing_ok=True)
        raise


def delete_document(db: Session, doc: RagDocument) -> None:
    path = Path(doc.stored_path)
    db.delete(doc)
    db.commit()
    path.unlink(missing_ok=True)

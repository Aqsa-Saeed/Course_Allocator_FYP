"""HTTP API: document upload/management, retrieval-only search, and the chat endpoint.
Every route is limited to the caller's department (see security.py)."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import llm
from .config import settings
from .db import get_db as get_rag_db
from .ingest import IngestError, delete_document, ingest
from .models import RagDocument
from .retrieval import build_search_query, detect_entities, retrieve
from .schemas import ChatRequest, ChatResponse, DocumentOut, SearchRequest, SourceOut
from .security import RagScope, get_rag_scope, require_rag_write

router = APIRouter(tags=["rag"])  # coordinators (read + chat)


def _source(n: int, h, cited: bool) -> SourceOut:
    snippet = h.text if len(h.text) <= 450 else h.text[:450].rsplit(" ", 1)[0] + "…"
    return SourceOut(
        n=n, cited=cited, document_id=h.document_id, title=h.title, doc_type=h.doc_type,
        page=h.page, course_code=h.course_code, instructor_name=h.instructor_name,
        semester=h.semester, score=h.score, snippet=snippet,
    )


def _get_doc(db: Session, doc_id: int, scope: RagScope) -> RagDocument:
    doc = db.get(RagDocument, doc_id)
    # A document from another department is reported as missing, not forbidden.
    if not doc or doc.department_id != scope.department_id:
        raise HTTPException(404, "Document not found.")
    return doc


# ----------------------------------------------------------------- documents
@router.post("/documents", response_model=DocumentOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    title: str | None = Form(None),
    course_id: int | None = Form(None),
    course_code: str | None = Form(None),
    instructor_id: int | None = Form(None),
    instructor_name: str | None = Form(None),
    semester: str | None = Form(None),
    scope: RagScope = Depends(require_rag_write),
    db: Session = Depends(get_rag_db),
):
    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    try:
        return ingest(
            db, department_id=scope.department_id, data=data, filename=file.filename or "document",
            doc_type=doc_type, title=title, course_id=course_id, course_code=course_code,
            instructor_id=instructor_id, instructor_name=instructor_name, semester=semester,
        )
    except IngestError as e:
        raise HTTPException(status_code=e.status, detail=str(e))


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    doc_type: str | None = None,
    instructor_id: int | None = None,
    course_code: str | None = None,
    scope: RagScope = Depends(get_rag_scope),
    db: Session = Depends(get_rag_db),
):
    stmt = (
        select(RagDocument)
        .where(RagDocument.department_id == scope.department_id)
        .order_by(RagDocument.uploaded_at.desc())
    )
    if doc_type:
        stmt = stmt.where(RagDocument.doc_type == doc_type)
    if instructor_id is not None:
        stmt = stmt.where(RagDocument.instructor_id == instructor_id)
    if course_code:
        stmt = stmt.where(RagDocument.course_code == course_code.upper())
    return db.scalars(stmt).all()


@router.get("/documents/{doc_id}/file")
def download_document(doc_id: int, scope: RagScope = Depends(get_rag_scope), db: Session = Depends(get_rag_db)):
    doc = _get_doc(db, doc_id, scope)
    path = Path(doc.stored_path)
    if not path.exists():
        raise HTTPException(410, "The original file is no longer on the server.")
    return FileResponse(path, filename=doc.filename, content_disposition_type="inline")


@router.delete("/documents/{doc_id}", status_code=204)
def remove_document(doc_id: int, scope: RagScope = Depends(require_rag_write), db: Session = Depends(get_rag_db)):
    delete_document(db, _get_doc(db, doc_id, scope))


@router.get("/meta")
def meta(scope: RagScope = Depends(get_rag_scope), db: Session = Depends(get_rag_db)):
    """Values for the filter dropdowns + a quick config check for the UI."""
    in_dept = RagDocument.department_id == scope.department_id
    instructors = db.execute(
        select(RagDocument.instructor_id, RagDocument.instructor_name)
        .where(in_dept, RagDocument.instructor_name.is_not(None)).distinct()
        .order_by(RagDocument.instructor_name)
    ).all()
    courses = db.scalars(
        select(RagDocument.course_code).where(in_dept, RagDocument.course_code.is_not(None))
        .distinct().order_by(RagDocument.course_code)
    ).all()
    total = db.scalar(select(func.count(RagDocument.id)).where(in_dept)) or 0
    return {
        "instructors": [{"id": i, "name": n} for i, n in instructors],
        "courses": courses,
        "document_count": total,
        "llm_configured": bool(settings.hf_token),
        "chat_model": settings.chat_model,
    }


# ------------------------------------------------------------------ retrieval
@router.post("/search")
def search(req: SearchRequest, scope: RagScope = Depends(get_rag_scope), db: Session = Depends(get_rag_db)):
    """Retrieval only (no LLM). Handy for checking what the index returns."""
    hits = retrieve(db, req.query, department_id=scope.department_id, top_k=req.top_k, doc_type=req.doc_type)
    return [_source(i, h, False) for i, h in enumerate(hits, start=1)]


# ----------------------------------------------------------------------- chat
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, scope: RagScope = Depends(get_rag_scope), db: Session = Depends(get_rag_db)):
    dept = scope.department_id
    if not db.scalar(select(func.count(RagDocument.id)).where(RagDocument.department_id == dept)):
        return ChatResponse(answer=llm.NO_DOCS_ANSWER, sources=[], grounded=False, scope={}, model=settings.chat_model)

    history = [t.model_dump() for t in req.history]
    explicit = bool(req.doc_type or req.instructor_id is not None or req.course_code or req.document_ids)

    detected = {"instructors": [], "courses": []} if explicit else detect_entities(db, req.message, dept)
    hits = retrieve(
        db,
        build_search_query(req.message, history),
        department_id=dept,
        top_k=req.top_k,
        doc_type=req.doc_type,
        instructor_id=req.instructor_id,
        course_code=req.course_code,
        document_ids=req.document_ids,
        auto_instructors=detected["instructors"],
        auto_courses=detected["courses"],
    )
    scope_info = {
        "doc_type": req.doc_type, "instructor_id": req.instructor_id,
        "course_code": req.course_code, "document_ids": req.document_ids,
        "auto_detected": detected if (detected["instructors"] or detected["courses"]) else None,
    }

    if not hits:
        return ChatResponse(answer=llm.NOT_FOUND_ANSWER, sources=[], grounded=False, scope=scope_info, model=settings.chat_model)

    try:
        raw = llm.generate(llm.build_messages(req.message, hits, history))
        answer, cited = llm.normalize_citations(raw, len(hits))
        warning = None if cited else "The model did not cite its sources. Check the passages below before relying on this answer."
    except llm.LLMError as e:
        # Degrade gracefully: still show the retrieved passages.
        answer, cited, warning = "I found relevant passages but couldn't generate a written answer. They are listed below.", [], str(e)

    return ChatResponse(
        answer=answer,
        sources=[_source(i, h, i in cited) for i, h in enumerate(hits, start=1)],
        grounded=True, scope=scope_info, model=settings.chat_model, warning=warning,
    )

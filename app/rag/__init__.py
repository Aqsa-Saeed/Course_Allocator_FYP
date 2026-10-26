"""RAG chat for the Course Allocation System.

Add to app/main.py (after the include_router loop):

    from app.rag import setup_rag
    setup_rag(app)

Access rules (see security.py): coordinators only, limited to their own department;
upload/delete need can_write.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"


def setup_rag(app: FastAPI, prefix: str = "/rag", mount_ui: bool = False) -> None:
    from .db import init_rag_schema
    from .router import router

    init_rag_schema()  # enables pgvector + creates rag_* tables if they don't exist
    app.include_router(router, prefix=prefix)
    if mount_ui:
        # Optional standalone page at /rag-ui/ (static files only; the API itself is protected).
        app.mount("/rag-ui", StaticFiles(directory=STATIC_DIR, html=True), name="rag-ui")

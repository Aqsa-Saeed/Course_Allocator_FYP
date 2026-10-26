"""Standalone DB engine/session for the RAG module (reads DATABASE_URL from .env)."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class RagBase(DeclarativeBase):
    """Separate metadata so this module never interferes with your existing models."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_rag_schema() -> None:
    """Idempotent: enables pgvector and creates rag_* tables if missing."""
    from . import models  # noqa: F401  (registers tables on RagBase.metadata)

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    RagBase.metadata.create_all(bind=engine)

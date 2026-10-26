from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import settings
from .db import RagBase


class RagDocument(RagBase):
    __tablename__ = "rag_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Every document belongs to the uploader's department; all reads are filtered by it.
    department_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(300))
    filename: Mapped[str] = mapped_column(String(300))
    stored_path: Mapped[str] = mapped_column(String(500))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), index=True)  # course_outline | faculty_feedback

    # Optional links to your existing data. Plain columns (no FK) so this module
    # works regardless of how your instructors/courses tables are defined.
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    course_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    instructor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    instructor_name: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)

    num_pages: Mapped[int] = mapped_column(Integer, default=0)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chunks: Mapped[list["RagChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class RagChunk(RagBase):
    __tablename__ = "rag_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("rag_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(settings.embedding_dim))

    document: Mapped[RagDocument] = relationship(back_populates="chunks")

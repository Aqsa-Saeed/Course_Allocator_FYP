from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    doc_type: str
    course_id: int | None = None
    course_code: str | None = None
    instructor_id: int | None = None
    instructor_name: str | None = None
    semester: str | None = None
    num_pages: int
    num_chunks: int
    uploaded_at: datetime


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=6000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = []
    doc_type: Literal["course_outline", "faculty_feedback"] | None = None
    instructor_id: int | None = None
    course_code: str | None = None
    document_ids: list[int] | None = None
    top_k: int | None = Field(default=None, ge=1, le=12)


class SourceOut(BaseModel):
    n: int                       # the [n] used in the answer text
    cited: bool                  # True if the answer actually references it
    document_id: int
    title: str
    doc_type: str
    page: int | None
    course_code: str | None
    instructor_name: str | None
    semester: str | None
    score: float
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    grounded: bool               # False when nothing relevant was retrieved
    scope: dict                  # filters that were applied (explicit + auto-detected)
    model: str
    warning: str | None = None   # e.g. the LLM was unreachable and only passages are shown


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    doc_type: Literal["course_outline", "faculty_feedback"] | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)

"""RAG settings. Everything is read from environment variables / your .env file."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class RagSettings:
    database_url: str = os.getenv("DATABASE_URL", "")

    # --- Hugging Face: embeddings (runs locally via sentence-transformers) ---
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    # MUST match the model's output size (all-MiniLM-L6-v2 = 384, bge-base = 768).
    embedding_dim: int = _int("RAG_EMBEDDING_DIM", 384)

    # --- Hugging Face: chat model (Inference API / Inference Providers) ---
    hf_token: str = os.getenv("HF_TOKEN", "") or os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
    chat_model: str = os.getenv("RAG_CHAT_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    max_new_tokens: int = _int("RAG_MAX_NEW_TOKENS", 600)
    temperature: float = _float("RAG_TEMPERATURE", 0.2)

    # --- Chunking ---
    chunk_size: int = _int("RAG_CHUNK_SIZE", 900)          # characters
    chunk_overlap: int = _int("RAG_CHUNK_OVERLAP", 150)    # characters

    # --- Retrieval ---
    top_k: int = _int("RAG_TOP_K", 5)
    min_score: float = _float("RAG_MIN_SCORE", 0.25)       # cosine similarity floor (0..1)
    max_chunks_per_doc: int = _int("RAG_MAX_CHUNKS_PER_DOC", 3)
    history_turns: int = _int("RAG_HISTORY_TURNS", 4)      # past user/assistant pairs sent to the LLM

    # --- Uploads ---
    upload_dir: Path = Path(os.getenv("RAG_UPLOAD_DIR", "uploads/rag"))
    max_upload_mb: int = _int("RAG_MAX_UPLOAD_MB", 20)


settings = RagSettings()
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
DOC_TYPES = {"course_outline", "faculty_feedback"}

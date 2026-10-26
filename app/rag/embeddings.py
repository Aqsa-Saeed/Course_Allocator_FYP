"""Hugging Face sentence-transformers embeddings (local, no API key needed)."""
import threading

from .config import settings

_model = None
_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(settings.embedding_model)
                dim = _model.get_sentence_embedding_dimension()
                if dim != settings.embedding_dim:
                    raise RuntimeError(
                        f"RAG_EMBEDDING_DIM={settings.embedding_dim} but "
                        f"{settings.embedding_model} outputs {dim} dimensions. "
                        "Fix RAG_EMBEDDING_DIM in .env (and recreate the rag_* tables)."
                    )
    return _model


def embed_documents(texts: list[str]) -> list[list[float]]:
    vecs = _get_model().encode(
        texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False
    )
    return [v.tolist() for v in vecs]


def embed_query(text: str) -> list[float]:
    return embed_documents([text])[0]

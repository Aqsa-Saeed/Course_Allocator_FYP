"""
Turns text into embedding vectors using sentence-transformers.

The model is loaded lazily (on first use) and cached, so importing this module
is cheap and the FastAPI app starts quickly. The first call downloads the model
(~90 MB) from Hugging Face; after that it is read from the local cache.
"""

from functools import lru_cache

from app.models.base import EMBEDDING_DIM

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer  # heavy import, kept lazy

    model = SentenceTransformer(MODEL_NAME)
    dimension = model.get_sentence_embedding_dimension()
    if dimension != EMBEDDING_DIM:
        raise RuntimeError(
            f"Model produces {dimension}-dimensional vectors but the database "
            f"columns hold {EMBEDDING_DIM}. Change EMBEDDING_DIM and re-migrate."
        )
    return model


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Embed many texts at once (much faster than one call per text)."""
    vectors = get_model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,   # unit length, so cosine similarity is well behaved
        show_progress_bar=False,
    )
    return [vector.tolist() for vector in vectors]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def instructor_text(instructor) -> str:
    """What we embed for an instructor: their specializations."""
    return (instructor.qualifications_text or "").strip()


def course_text(course) -> str:
    """What we embed for a course: its title plus what it needs from an instructor."""
    return f"{course.title}. {(course.requirements_text or '').strip()}".strip()

"""Answer generation through the Hugging Face Inference API, grounded in retrieved chunks."""
import re

from .config import settings
from .retrieval import Hit

SYSTEM_PROMPT = """You are the assistant inside a university Course Allocation System. \
Coordinators ask you about course outlines and about student feedback on faculty members.

Rules:
1. Answer ONLY from the numbered context passages provided. Never use outside knowledge about the course or the faculty member.
2. After every claim, cite the passage(s) it came from using square brackets, e.g. [1] or [2][3]. Use only the numbers provided.
3. If the passages do not contain the answer, say so plainly and mention what is missing. Do not guess.
4. When passages disagree (for example two semesters of feedback), say so and attribute each view to its source.
5. Feedback about people is sensitive: report what the documents say, stay neutral, and do not add opinions or judgements of your own.
6. Be concise. Use short paragraphs or bullet points."""

NO_DOCS_ANSWER = "No documents have been uploaded yet. Upload a course outline or faculty feedback file first, then ask again."
NOT_FOUND_ANSWER = (
    "I couldn't find anything relevant to that in the uploaded documents. "
    "Try rephrasing, naming the course code or faculty member, or removing filters."
)


class LLMError(Exception):
    """Raised with a user-readable message when the Hugging Face call fails."""


def _label(h: Hit) -> str:
    kind = "Course outline" if h.doc_type == "course_outline" else "Faculty feedback"
    bits = [kind, h.title]
    if h.instructor_name:
        bits.append(h.instructor_name)
    if h.course_code:
        bits.append(h.course_code)
    if h.semester:
        bits.append(h.semester)
    if h.page:
        bits.append(f"p.{h.page}")
    return ", ".join(bits)


def build_messages(question: str, hits: list[Hit], history: list[dict]) -> list[dict]:
    context = "\n\n".join(f"[{i}] ({_label(h)})\n{h.text}" for i, h in enumerate(hits, start=1))
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    keep = history[-(settings.history_turns * 2):]
    messages.extend({"role": m["role"], "content": m["content"]} for m in keep)
    messages.append(
        {"role": "user", "content": f"Context passages:\n\n{context}\n\nQuestion: {question}"}
    )
    return messages


def generate(messages: list[dict]) -> str:
    if not settings.hf_token:
        raise LLMError(
            "HF_TOKEN is not set. Create a free token at huggingface.co/settings/tokens "
            "and add HF_TOKEN=... to your .env, then restart the server."
        )
    from huggingface_hub import InferenceClient

    try:
        client = InferenceClient(model=settings.chat_model, token=settings.hf_token, timeout=90)
        resp = client.chat_completion(
            messages=messages,
            max_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:  # map common failures to something a user can act on
        text = str(e).lower()
        if "401" in text or "unauthorized" in text or ("invalid" in text and "token" in text):
            raise LLMError("Hugging Face rejected the token. Check HF_TOKEN in your .env.")
        if "403" in text or "gated" in text or ("access" in text and "denied" in text):
            raise LLMError(
                f"Your token can't use {settings.chat_model}. Accept the model's terms on "
                "huggingface.co or switch RAG_CHAT_MODEL to another model."
            )
        if "404" in text or "not found" in text or "not supported" in text:
            raise LLMError(
                f"{settings.chat_model} isn't available on Hugging Face's inference service right now. "
                "Set RAG_CHAT_MODEL to another chat model."
            )
        if "429" in text or "rate limit" in text or "quota" in text or "402" in text:
            raise LLMError("Hugging Face rate limit or free credits reached. Wait a bit and retry.")
        raise LLMError(f"The language model request failed: {e}")


_CITE = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")


def normalize_citations(answer: str, n_sources: int) -> tuple[str, list[int]]:
    """Rewrites '[1, 2]' as '[1][2]', removes references to sources that don't exist,
    and returns the ordered list of source numbers actually cited."""
    cited: list[int] = []

    def repl(m: re.Match) -> str:
        nums = [int(x) for x in re.split(r"[,;]", m.group(1))]
        valid = [n for n in nums if 1 <= n <= n_sources]
        for n in valid:
            if n not in cited:
                cited.append(n)
        return "".join(f"[{n}]" for n in valid)

    return _CITE.sub(repl, answer), cited

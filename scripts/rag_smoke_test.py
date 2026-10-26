"""Run against a live server:
    RAG_TOKEN=<jwt> python scripts/rag_smoke_test.py path/to/outline.pdf [http://127.0.0.1:8000]
(on Windows PowerShell:  $env:RAG_TOKEN="<jwt>"; python scripts/rag_smoke_test.py outline.pdf)

Get a token with a coordinator account (needs can_write to upload):
    curl -X POST http://127.0.0.1:8000/auth/login -d "username=YOU&password=PASS"
Uploads the file, runs a retrieval-only search, then asks one chat question."""
import json
import os
import mimetypes
import sys
import urllib.request
import uuid
from pathlib import Path

path = Path(sys.argv[1])
base = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000").rstrip("/")
AUTH = {"Authorization": f"Bearer {os.environ['RAG_TOKEN']}"} if os.environ.get("RAG_TOKEN") else {}


def post_json(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json", **AUTH})
    return json.load(urllib.request.urlopen(req))


def upload(url, file_path, fields):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n".encode() + file_path.read_bytes() + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(url, b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={boundary}", **AUTH})
    return json.load(urllib.request.urlopen(req))


print("Uploading…")
try:
    doc = upload(f"{base}/rag/documents", path, {"doc_type": "course_outline", "course_code": "TEST-101"})
    print("  ->", doc["title"], f'({doc["num_chunks"]} chunks)')
except urllib.error.HTTPError as e:
    print("  upload:", e.read().decode())

print("Search (no LLM)…")
for s in post_json(f"{base}/rag/search", {"query": "grading and assessment"}):
    print(f'  [{s["n"]}] {s["score"]:.2f} p.{s["page"]} {s["snippet"][:90]!r}')

print("Chat…")
r = post_json(f"{base}/rag/chat", {"message": "What are the grading components?"})
print(r["answer"])
if r.get("warning"):
    print("WARNING:", r["warning"])

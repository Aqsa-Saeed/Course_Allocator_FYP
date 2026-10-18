"""
FastAPI entry point. Run with:
    uvicorn app.main:app --reload
from the project root (the folder that contains app/).
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    allocations, audit, auth, courses, departments, faculty, instructors, me, preferences,
    programs, ranking, sections, semesters, settings,
)

app = FastAPI(title="Course Allocation API")

# The React app runs on a different port, so the browser needs the backend's
# permission to call it. Add more addresses with CORS_ORIGINS="a,b" in .env if needed.
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, me, departments, programs, semesters, courses, sections, instructors,
               preferences, faculty, audit, ranking, allocations, settings):
    app.include_router(module.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "course-allocation-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}

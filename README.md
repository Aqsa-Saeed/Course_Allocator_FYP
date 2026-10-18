# Course Allocation System — Backend Setup

## 1. Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
```

## 2. Install dependencies
```bash
pip install -r requirements.txt
```

## 3. Set up PostgreSQL
- Make sure Postgres is running and pgvector is installed (see your earlier setup notes if starting fresh on Windows).
- Create the database:
```sql
CREATE DATABASE course_allocation;
\c course_allocation
CREATE EXTENSION vector;
```

## 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your real values:
```bash
copy .env.example .env        # macOS/Linux: cp .env.example .env
```
Edit `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/course_allocation
SECRET_KEY=<generate one: python -c "import secrets; print(secrets.token_hex(32))">
```

Also update the `sqlalchemy.url` line in `alembic.ini` to match your `DATABASE_URL` — Alembic reads that file directly, not `.env`.

## 5. Run the migration
Alembic is already initialized and wired to `app/models` — no `alembic init` needed.
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## 6. Verify
```bash
psql -U postgres -d course_allocation -c "\dt"
```
You should see 15 tables: departments, programs, semesters, courses, sections,
course_prerequisites, instructors, users, instructor_history, feedback_scores,
workload, instructor_preferences, allocations, audit_logs, ranking_settings
(plus alembic_version).

## 7. Run the API
```bash
-
```
Open http://127.0.0.1:8000/docs

## Schema overview
- **Academic structure**: Department → Program → Course → Section, with Semester and CoursePrerequisite
- **People**: Instructor, User (coordinators — role = department_coordinator | program_coordinator)
- **History & feedback**: InstructorHistory, FeedbackScore, Workload — all keyed to Section/Semester
- **Preferences**: InstructorPreference (Course-level, not Section-level)
- **Allocation**: Allocation (the finalized Section→Instructor assignment) + AuditLog (who/what/when)
- **Config**: RankingSettings (single-row, holds scoring weights + policy thresholds)

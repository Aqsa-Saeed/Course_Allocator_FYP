"""
Creates the single ranking_settings row (scoring weights and policy limits)
with sensible defaults. Safe to run more than once: an existing row is left
untouched, so any weights you have tuned are never overwritten.

From the project root, venv active:
    python -m scripts.seed_ranking_settings
"""

from app.database import SessionLocal
from app.models import RankingSettings


def main():
    db = SessionLocal()
    try:
        settings = db.query(RankingSettings).first()
        if settings is None:
            settings = RankingSettings()
            db.add(settings)
            db.commit()
            db.refresh(settings)
            print("Created ranking settings.")
        else:
            print("Ranking settings already exist, left unchanged.")
        print(
            f"Weights: expertise {settings.weight_content_match}, history {settings.weight_history}, "
            f"recency {settings.weight_recency}, feedback {settings.weight_feedback}, "
            f"preference {settings.weight_preference}, workload {settings.weight_workload}"
        )
        print(f"Policy: min feedback {settings.min_feedback_score}, "
              f"max sections per instructor {settings.max_courses_per_instructor}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

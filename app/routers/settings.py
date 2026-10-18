"""
The scoring weights and the two policy limits (workload cap, minimum feedback).
Everyone with coordinator access can read them; only Department Coordinators
can change them, and every change is written to the audit log.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.access import Scope, get_scope, require_writer
from app.database import get_db
from app.schemas.settings import WEIGHT_FIELDS, RankingSettingsOut, RankingSettingsUpdate
from app.services.audit import log_action
from app.services.ranking import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])


def _load(db):
    try:
        return get_settings(db)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


@router.get("/ranking", response_model=RankingSettingsOut)
def read_settings(scope: Scope = Depends(get_scope), db: Session = Depends(get_db)):
    return _load(db)


@router.patch("/ranking", response_model=RankingSettingsOut)
def update_settings(payload: RankingSettingsUpdate, scope: Scope = Depends(require_writer),
                    db: Session = Depends(get_db)):
    settings = _load(db)
    changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}

    merged = {f: changes.get(f, getattr(settings, f)) for f in WEIGHT_FIELDS}
    if sum(merged.values()) <= 0:
        raise HTTPException(status_code=422, detail="At least one weight must be above zero.")

    differences = []
    for field, new in changes.items():
        old = getattr(settings, field)
        if old != new:
            differences.append(f"{field} {old:g} -> {new:g}")
            setattr(settings, field, new)
    if differences:
        log_action(db, scope.user, "ranking_settings_updated", "RankingSettings", settings.id,
                   "; ".join(differences))
    db.commit()
    db.refresh(settings)
    return settings

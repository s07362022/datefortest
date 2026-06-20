from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.preference import Preference
from app.models.user import User
from app.schemas.preference import PreferenceOut, PreferenceUpdate

router = APIRouter(prefix="/preferences", tags=["Preferences"])


def _get_or_create_preference(db: Session, user_id: int) -> Preference:
    pref = db.query(Preference).filter(Preference.user_id == user_id).first()
    if not pref:
        pref = Preference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def _pref_to_out(pref: Preference) -> PreferenceOut:
    return PreferenceOut(
        id=pref.id,
        user_id=pref.user_id,
        min_age=pref.min_age,
        max_age=pref.max_age,
        max_distance_km=pref.max_distance_km,
        preferred_genders=pref.preferred_genders.split(","),
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )


@router.get("/me", response_model=PreferenceOut)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's match preferences."""
    pref = _get_or_create_preference(db, current_user.id)
    return _pref_to_out(pref)


@router.put("/me", response_model=PreferenceOut)
def update_preferences(
    body: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update match preferences for the current user."""
    pref = _get_or_create_preference(db, current_user.id)

    if body.min_age is not None:
        pref.min_age = body.min_age
    if body.max_age is not None:
        pref.max_age = body.max_age
    if body.max_distance_km is not None:
        pref.max_distance_km = body.max_distance_km
    if body.preferred_genders is not None:
        pref.preferred_genders = ",".join(body.preferred_genders)

    db.commit()
    db.refresh(pref)
    return _pref_to_out(pref)

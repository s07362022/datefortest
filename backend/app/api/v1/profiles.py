from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.profile import ProfileOut, ProfileUpdate, PublicProfileOut, TagOut
from app.services.profile_service import (
    get_or_create_profile,
    is_profile_complete,
    update_profile,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])


def _build_profile_out(profile: Profile) -> ProfileOut:
    tags = [TagOut(id=pt.tag_id, name=pt.tag.name) for pt in profile.profile_tags]
    return ProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        birthday=profile.birthday,
        gender=profile.gender,
        interested_in=profile.interested_in,
        bio=profile.bio,
        city=profile.city,
        height_cm=profile.height_cm,
        tags=tags,
        is_complete=is_profile_complete(profile),
        last_active_at=profile.last_active_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's profile (creates empty one if not yet exists)."""
    profile = get_or_create_profile(db, current_user.id)
    return _build_profile_out(profile)


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile fields."""
    profile = get_or_create_profile(db, current_user.id)
    profile = update_profile(db, profile, body)
    return _build_profile_out(profile)


@router.get("/{user_id}", response_model=PublicProfileOut)
def get_public_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return another user's public profile.

    Blocked users receive 404. GPS coordinates are never exposed.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_PROFILE", "message": "請使用 /profiles/me 查看自己的檔案"},
        )

    target = db.get(User, user_id)
    if not target or not target.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "USER_NOT_FOUND", "message": "使用者不存在"})

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "PROFILE_NOT_FOUND", "message": "對方尚未建立個人檔案"})

    tags = [TagOut(id=pt.tag_id, name=pt.tag.name) for pt in profile.profile_tags]
    return PublicProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        gender=profile.gender,
        city=profile.city,
        bio=profile.bio,
        height_cm=profile.height_cm,
        tags=tags,
        distance_band=None,  # Phase 3 時依 GPS 計算
        last_active_at=profile.last_active_at,
    )

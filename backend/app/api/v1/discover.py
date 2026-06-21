from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.discover import DiscoverItem, DiscoverResponse
from app.schemas.profile import TagOut
from app.services.discover_service import get_discover_candidates
from app.services.profile_service import is_profile_complete, get_or_create_profile

router = APIRouter(prefix="/discover", tags=["Discover"])


def _age(birthday: date) -> int:
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


@router.get("", response_model=DiscoverResponse)
def discover(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return recommended users for the current user.

    Requires a complete profile (per SPEC §4.2).
    Results are scored by profile completeness, recent activity,
    distance, and shared interests.
    """
    profile = get_or_create_profile(db, current_user.id)
    if not is_profile_complete(profile):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PROFILE_INCOMPLETE", "message": "請先完成個人檔案才能使用探索功能"},
        )

    candidates = get_discover_candidates(db, current_user, limit=limit, cursor=cursor)

    items = []
    for c in candidates:
        p = c["profile"]
        tags = [TagOut(id=pt.tag_id, name=pt.tag.name) for pt in p.profile_tags]
        age = _age(p.birthday) if p.birthday else None
        primary = c.get("primary_photo")
        items.append(DiscoverItem(
            user_id=c["user"].id,
            display_name=p.display_name,
            gender=p.gender,
            city=p.city,
            bio=p.bio,
            height_cm=p.height_cm,
            age=age,
            distance_band=c["distance_band"],
            tags=tags,
            primary_photo_path=primary.file_path if primary else None,
            last_active_at=p.last_active_at,
        ))

    next_cursor = candidates[-1]["user"].id if len(candidates) == limit else None
    return DiscoverResponse(items=items, next_cursor=next_cursor, total=len(items))

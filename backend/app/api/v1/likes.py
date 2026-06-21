from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.match import Match
from app.models.photo import ModerationStatusEnum
from app.models.profile import Profile
from app.models.user import User
from app.schemas.like import DailyLikeStatus, LikeResponse, MatchOut, PassResponse
from app.services.like_service import (
    get_daily_like_count,
    get_matches,
    like_user,
    pass_user,
    unmatch,
)

router = APIRouter(tags=["Likes & Matches"])


# ── Like / Pass ───────────────────────────────────────────────────────────────

@router.post("/likes/{to_user_id}", response_model=LikeResponse, status_code=status.HTTP_200_OK)
def like(
    to_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Like a user. If mutual, a Match is created automatically.

    Returns is_match: true and match_id when a new match is formed.
    Returns 429 when daily like limit is reached.
    """
    result = like_user(db, current_user.id, to_user_id)
    msg = "配對成功！" if result["is_match"] else "已送出喜歡"
    return LikeResponse(is_match=result["is_match"], match_id=result["match_id"], message=msg)


@router.post("/passes/{to_user_id}", response_model=PassResponse, status_code=status.HTTP_200_OK)
def pass_(
    to_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pass (skip) a user. They will no longer appear in your discover feed."""
    pass_user(db, current_user.id, to_user_id)
    return PassResponse(message="已略過")


@router.get("/likes/quota", response_model=DailyLikeStatus)
def like_quota(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return today's like usage and remaining quota."""
    used = get_daily_like_count(db, current_user.id)
    limit = settings.daily_like_limit
    now_utc = datetime.now(timezone.utc)
    resets_at = now_utc.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT00:00:00Z")
    # tomorrow's reset
    from datetime import timedelta
    resets_at = (now_utc.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return DailyLikeStatus(used=used, limit=limit, remaining=max(0, limit - used), resets_at=resets_at)


# ── Matches ───────────────────────────────────────────────────────────────────

@router.get("/matches", response_model=list[MatchOut])
def list_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all active matches, newest first."""
    matches = get_matches(db, current_user.id)
    result = []
    for m in matches:
        other_id = m.user2_id if m.user1_id == current_user.id else m.user1_id
        profile = db.query(Profile).filter(Profile.user_id == other_id).first()
        primary = None
        if profile:
            other_user = db.get(User, other_id)
            if other_user:
                primary_photo = next(
                    (p for p in other_user.photos
                     if p.moderation_status in (ModerationStatusEnum.pending, ModerationStatusEnum.approved)
                     and p.is_primary),
                    None,
                )
                if primary_photo:
                    primary = primary_photo.file_path

        result.append(MatchOut(
            id=m.id,
            other_user_id=other_id,
            other_display_name=profile.display_name if profile else None,
            other_primary_photo=primary,
            is_active=m.is_active,
            created_at=m.created_at,
        ))
    return result


@router.delete("/matches/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def unmatch_route(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unmatch (soft-delete). The match disappears from both users' lists."""
    unmatch(db, match_id, current_user.id)

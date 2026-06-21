from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.like import Like, LikeActionEnum
from app.models.match import Match


# ── Helpers ───────────────────────────────────────────────────────────────────

def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _match_ids(user1_id: int, user2_id: int) -> tuple[int, int]:
    """Return (smaller_id, larger_id) to enforce the uq_match_pair constraint."""
    return (min(user1_id, user2_id), max(user1_id, user2_id))


# ── Like quota ────────────────────────────────────────────────────────────────

def get_daily_like_count(db: Session, user_id: int) -> int:
    """Return number of 'like' actions the user has made today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Like)
        .filter(
            Like.from_user_id == user_id,
            Like.action == LikeActionEnum.like,
            Like.created_at >= today_start,
        )
        .count()
    )


# ── Like ──────────────────────────────────────────────────────────────────────

def like_user(db: Session, from_user_id: int, to_user_id: int) -> dict:
    """Record a like action. Returns {'is_match': bool, 'match_id': int | None}.

    Rules:
    - Cannot like yourself.
    - Cannot like someone you've already acted on.
    - Daily like quota enforced (configurable via settings.daily_like_limit).
    - If the target already liked you, creates a Match automatically.
    """
    if from_user_id == to_user_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "SELF_LIKE", "message": "不能對自己按喜歡"},
        )

    existing = db.query(Like).filter(
        Like.from_user_id == from_user_id, Like.to_user_id == to_user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "ALREADY_ACTED", "message": "已經對此用戶執行過操作"},
        )

    if settings.like_limit_enabled:
        daily_count = get_daily_like_count(db, from_user_id)
        if daily_count >= settings.daily_like_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "DAILY_LIMIT_REACHED",
                    "message": f"今日喜歡次數已達上限（{settings.daily_like_limit} 次），明日 00:00 UTC 重置",
                },
            )

    db.add(Like(from_user_id=from_user_id, to_user_id=to_user_id, action=LikeActionEnum.like))
    db.flush()

    # Check for mutual like
    mutual = db.query(Like).filter(
        Like.from_user_id == to_user_id,
        Like.to_user_id == from_user_id,
        Like.action == LikeActionEnum.like,
    ).first()

    match_id = None
    if mutual:
        uid1, uid2 = _match_ids(from_user_id, to_user_id)
        existing_match = db.query(Match).filter(
            Match.user1_id == uid1, Match.user2_id == uid2
        ).first()
        if not existing_match:
            new_match = Match(user1_id=uid1, user2_id=uid2, is_active=True)
            db.add(new_match)
            db.flush()
            match_id = new_match.id
        else:
            # Reactivate if previously unmatched
            if not existing_match.is_active:
                existing_match.is_active = True
            match_id = existing_match.id

    db.commit()
    return {"is_match": mutual is not None, "match_id": match_id}


# ── Pass ──────────────────────────────────────────────────────────────────────

def pass_user(db: Session, from_user_id: int, to_user_id: int) -> None:
    """Record a pass action. Idempotent — silently ignores if already passed."""
    if from_user_id == to_user_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "SELF_PASS", "message": "不能略過自己"},
        )

    existing = db.query(Like).filter(
        Like.from_user_id == from_user_id, Like.to_user_id == to_user_id
    ).first()
    if existing:
        return  # Already acted, silently succeed

    db.add(Like(from_user_id=from_user_id, to_user_id=to_user_id, action=LikeActionEnum.pass_))
    db.commit()


# ── Match ─────────────────────────────────────────────────────────────────────

def get_matches(db: Session, user_id: int) -> list[Match]:
    """Return all active matches for a user."""
    return (
        db.query(Match)
        .filter(
            Match.is_active == True,
            (Match.user1_id == user_id) | (Match.user2_id == user_id),
        )
        .order_by(Match.created_at.desc())
        .all()
    )


def unmatch(db: Session, match_id: int, user_id: int) -> None:
    """Soft-delete a match (set is_active = False)."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail={"code": "MATCH_NOT_FOUND", "message": "配對不存在"})
    if match.user1_id != user_id and match.user2_id != user_id:
        raise HTTPException(status_code=403, detail={"code": "NOT_YOUR_MATCH", "message": "無權操作此配對"})
    if not match.is_active:
        raise HTTPException(status_code=404, detail={"code": "MATCH_NOT_FOUND", "message": "配對不存在"})

    match.is_active = False
    db.commit()

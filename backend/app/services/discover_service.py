from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, not_, or_, select
from sqlalchemy.orm import Session

from app.models.photo import ModerationStatusEnum, Photo
from app.models.preference import Preference
from app.models.profile import Profile
from app.models.tag import ProfileTag
from app.models.user import User
from app.services.profile_service import haversine_km, distance_band


def _age(birthday: date) -> int:
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))


def _recent_active_score(last_active_at: Optional[datetime]) -> float:
    """Score 0-20 based on how recently the user was active."""
    if not last_active_at:
        return 0
    hours_ago = (datetime.now(timezone.utc) - last_active_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
    if hours_ago < 1:
        return 20
    if hours_ago < 24:
        return 15
    if hours_ago < 72:
        return 10
    if hours_ago < 168:
        return 5
    return 0


def _distance_score(dist_km: Optional[float], max_km: int) -> float:
    """Score 0-20: closer = higher score."""
    if dist_km is None:
        return 10  # neutral if no GPS
    ratio = dist_km / max(max_km, 1)
    return max(0, 20 * (1 - ratio))


def _shared_interest_score(my_tag_ids: set[int], their_tag_ids: set[int]) -> float:
    """Score 0-20 based on shared interest tags."""
    shared = len(my_tag_ids & their_tag_ids)
    return min(shared * 5, 20)


def get_discover_candidates(
    db: Session,
    current_user: User,
    limit: int = 20,
    cursor: Optional[int] = None,
) -> list[dict]:
    """Return scored and filtered discover candidates.

    Scoring formula (max 100):
      profile_complete_score (0-100, stored field)
      + recent_active_score  (0-20)
      + distance_score       (0-20)
      + shared_interest_score(0-20)

    Tie-break: score DESC, last_active_at DESC, created_at DESC, user_id ASC
    """
    me_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    me_prefs = db.query(Preference).filter(Preference.user_id == current_user.id).first()

    my_tag_ids: set[int] = set()
    if me_profile:
        my_tag_ids = {pt.tag_id for pt in me_profile.profile_tags}

    max_km = me_prefs.max_distance_km if me_prefs else 50
    min_age = me_prefs.min_age if me_prefs else 18
    max_age = me_prefs.max_age if me_prefs else 99
    pref_genders = set(me_prefs.preferred_genders.split(",")) if me_prefs else {"everyone"}

    # Subquery: users already liked/passed by current user
    liked_ids_subq = None
    try:
        from app.models.like import Like  # Phase 3 model
        liked_ids_subq = select(Like.to_user_id).where(Like.from_user_id == current_user.id)
    except Exception:
        pass

    # Subquery: blocked users (both directions)
    blocked_ids_subq = None
    blocking_ids_subq = None
    try:
        from app.models.block import Block  # Phase 6 model
        blocked_ids_subq = select(Block.blocked_id).where(Block.blocker_id == current_user.id)
        blocking_ids_subq = select(Block.blocker_id).where(Block.blocked_id == current_user.id)
    except Exception:
        pass

    # Base query: active users with complete-enough profiles
    query = (
        db.query(User, Profile)
        .join(Profile, Profile.user_id == User.id)
        .filter(
            User.is_active == True,
            User.id != current_user.id,
        )
    )

    if liked_ids_subq is not None:
        query = query.filter(not_(User.id.in_(liked_ids_subq)))
    if blocked_ids_subq is not None:
        query = query.filter(
            not_(User.id.in_(blocked_ids_subq)),
            not_(User.id.in_(blocking_ids_subq)),
        )

    if cursor:
        query = query.filter(User.id > cursor)

    rows = query.all()

    results = []
    for user, profile in rows:
        if not profile.birthday:
            continue
        age = _age(profile.birthday)
        if not (min_age <= age <= max_age):
            continue

        # Gender filter
        if "everyone" not in pref_genders and profile.gender:
            gender_val = profile.gender.value if hasattr(profile.gender, "value") else profile.gender
            if gender_val not in pref_genders:
                continue

        # Distance
        dist_km = None
        band = None
        if me_profile and me_profile.latitude and me_profile.longitude and profile.latitude and profile.longitude:
            dist_km = haversine_km(me_profile.latitude, me_profile.longitude, profile.latitude, profile.longitude)
            if dist_km > max_km:
                continue
            band = distance_band(dist_km)

        # Has at least one visible photo
        visible_photos = [
            p for p in user.photos
            if p.moderation_status in (ModerationStatusEnum.pending, ModerationStatusEnum.approved)
        ]

        # Profile complete score (simplified for discover)
        pc_score = _calc_profile_complete_score(profile, visible_photos)
        ra_score = _recent_active_score(profile.last_active_at)
        ds_score = _distance_score(dist_km, max_km)
        their_tags = {pt.tag_id for pt in profile.profile_tags}
        si_score = _shared_interest_score(my_tag_ids, their_tags)

        total_score = pc_score * 0.4 + ra_score + ds_score + si_score

        results.append({
            "user": user,
            "profile": profile,
            "distance_band": band,
            "score": total_score,
            "primary_photo": next((p for p in visible_photos if p.is_primary), visible_photos[0] if visible_photos else None),
        })

    # Sort: score DESC, last_active_at DESC, created_at DESC, user_id ASC
    results.sort(key=lambda r: (
        -r["score"],
        -(r["profile"].last_active_at.timestamp() if r["profile"].last_active_at else 0),
        -(r["profile"].created_at.timestamp()),
        r["user"].id,
    ))

    return results[:limit]


def _calc_profile_complete_score(profile: Profile, photos: list) -> float:
    """Calculate profile_complete_score (0-100) per SPEC §4.2."""
    score = 0
    if profile.display_name:
        score += 10
    if profile.birthday:
        score += 10
    if profile.gender:
        score += 10
    if profile.interested_in:
        score += 10
    if profile.city:
        score += 10
    if profile.bio and len(profile.bio.strip()) >= 20:
        score += 20
    if photos:
        score += 20
    if len(profile.profile_tags) >= 3:
        score += 10
    return score

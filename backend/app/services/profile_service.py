from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.tag import ProfileTag, Tag
from app.schemas.profile import ProfileUpdate


# ── Profile completeness ──────────────────────────────────────────────────────

def is_profile_complete(profile: Profile) -> bool:
    """Check whether a profile meets all required completion conditions.

    Conditions (per SPEC §4.2):
    - display_name required
    - birthday required + age >= 18
    - gender required
    - interested_in required
    - city required
    - bio >= 20 Chinese characters or 40 English characters
    - at least 1 photo with status pending or approved
    - at least 3 interest tags
    """
    if not profile.display_name:
        return False
    if not profile.birthday or not _is_adult(profile.birthday):
        return False
    if not profile.gender:
        return False
    if not profile.interested_in:
        return False
    if not profile.city:
        return False
    if not profile.bio or not _bio_long_enough(profile.bio):
        return False
    active_photos = [
        p for p in profile.user.photos
        if p.moderation_status in ("pending", "approved")
    ]
    if len(active_photos) < 1:
        return False
    if len(profile.profile_tags) < 3:
        return False
    return True


def _is_adult(birthday: date) -> bool:
    today = date.today()
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    return age >= 18


def _bio_long_enough(bio: str) -> bool:
    """Return True if bio meets minimum length (20 CJK chars or 40 other chars)."""
    text = bio.strip()
    cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    non_cjk = len(text) - cjk_count
    return cjk_count >= 20 or (cjk_count * 2 + non_cjk) >= 40


# ── Profile CRUD ──────────────────────────────────────────────────────────────

def get_or_create_profile(db: Session, user_id: int) -> Profile:
    """Return existing profile or create an empty one."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, profile: Profile, data: ProfileUpdate) -> Profile:
    """Apply updates from ProfileUpdate schema to the profile."""
    update_fields = data.model_dump(exclude_unset=True, exclude={"tag_ids"})

    if "birthday" in update_fields and update_fields["birthday"]:
        if not _is_adult(update_fields["birthday"]):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail={"code": "AGE_RESTRICTION", "message": "年齡必須滿 18 歲"},
            )

    for field, value in update_fields.items():
        setattr(profile, field, value)

    if data.tag_ids is not None:
        db.query(ProfileTag).filter(ProfileTag.profile_id == profile.id).delete()
        for tag_id in data.tag_ids:
            tag = db.get(Tag, tag_id)
            if tag:
                db.add(ProfileTag(profile_id=profile.id, tag_id=tag_id))

    profile.last_active_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile


# ── Distance band ─────────────────────────────────────────────────────────────

def distance_band(km: float | None) -> str | None:
    """Convert a distance in km to a display band per SPEC §4.2."""
    if km is None:
        return None
    if km < 1:
        return "< 1km"
    if km < 5:
        return "1-5km"
    if km < 10:
        return "5-10km"
    if km < 25:
        return "10-25km"
    if km < 50:
        return "25-50km"
    return "50km+"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance between two GPS coordinates in km."""
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))

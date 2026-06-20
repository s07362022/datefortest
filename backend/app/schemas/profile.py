from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.profile import GenderEnum, InterestedInEnum


# ── Tag ──────────────────────────────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    birthday: Optional[date] = None
    gender: Optional[GenderEnum] = None
    interested_in: Optional[InterestedInEnum] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    height_cm: Optional[int] = None
    tag_ids: Optional[list[int]] = None

    @field_validator("bio")
    @classmethod
    def bio_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) > 500:
            raise ValueError("自我介紹不得超過 500 字元")
        return v

    @field_validator("height_cm")
    @classmethod
    def height_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (100 <= v <= 250):
            raise ValueError("身高請填寫 100～250 cm")
        return v


class ProfileOut(BaseModel):
    id: int
    user_id: int
    display_name: Optional[str]
    birthday: Optional[date]
    gender: Optional[GenderEnum]
    interested_in: Optional[InterestedInEnum]
    bio: Optional[str]
    city: Optional[str]
    height_cm: Optional[int]
    tags: list[TagOut] = []
    is_complete: bool = False
    last_active_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicProfileOut(BaseModel):
    """Profile seen by other users — no GPS, only distance band."""
    id: int
    user_id: int
    display_name: Optional[str]
    gender: Optional[GenderEnum]
    city: Optional[str]
    bio: Optional[str]
    height_cm: Optional[int]
    tags: list[TagOut] = []
    distance_band: Optional[str] = None   # e.g. "1-5km"
    last_active_at: Optional[datetime]

    model_config = {"from_attributes": True}

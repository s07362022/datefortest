from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.profile import GenderEnum
from app.schemas.photo import PhotoOut
from app.schemas.profile import TagOut


class DiscoverItem(BaseModel):
    user_id: int
    display_name: Optional[str]
    gender: Optional[GenderEnum]
    city: Optional[str]
    bio: Optional[str]
    height_cm: Optional[int]
    age: Optional[int]
    distance_band: Optional[str]
    tags: list[TagOut] = []
    primary_photo_path: Optional[str] = None
    last_active_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DiscoverResponse(BaseModel):
    items: list[DiscoverItem]
    next_cursor: Optional[int] = None
    total: int

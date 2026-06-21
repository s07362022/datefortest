from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.like import LikeActionEnum


class LikeResponse(BaseModel):
    """Response for POST /likes/{user_id}."""
    is_match: bool
    match_id: Optional[int] = None
    message: str


class PassResponse(BaseModel):
    """Response for POST /passes/{user_id}."""
    message: str


class MatchOut(BaseModel):
    """A match record with the other user's basic profile."""
    id: int
    other_user_id: int
    other_display_name: Optional[str] = None
    other_primary_photo: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyLikeStatus(BaseModel):
    """Current daily like usage."""
    used: int
    limit: int
    remaining: int
    resets_at: str

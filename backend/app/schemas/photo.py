from datetime import datetime

from pydantic import BaseModel

from app.models.photo import ModerationStatusEnum


class PhotoOut(BaseModel):
    id: int
    user_id: int
    file_path: str
    sort_order: int
    is_primary: bool
    moderation_status: ModerationStatusEnum
    created_at: datetime

    model_config = {"from_attributes": True}

from datetime import datetime

from pydantic import BaseModel, field_validator


class MessageOut(BaseModel):
    id: int
    match_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageOut]
    next_cursor: int | None = None


class ReadResponse(BaseModel):
    marked_read: int

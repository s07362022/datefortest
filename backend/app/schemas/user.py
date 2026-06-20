from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.schemas.profile import ProfileOut


class UserOut(BaseModel):
    """Current user response — includes own profile."""
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
    profile: Optional[ProfileOut] = None

    model_config = {"from_attributes": True}

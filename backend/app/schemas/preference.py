from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


VALID_GENDERS = {"women", "men", "non_binary", "everyone"}


class PreferenceUpdate(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    max_distance_km: Optional[int] = None
    preferred_genders: Optional[list[str]] = None

    @field_validator("min_age")
    @classmethod
    def min_age_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (18 <= v <= 99):
            raise ValueError("最小年齡需在 18～99 之間")
        return v

    @field_validator("max_age")
    @classmethod
    def max_age_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (18 <= v <= 99):
            raise ValueError("最大年齡需在 18～99 之間")
        return v

    @field_validator("max_distance_km")
    @classmethod
    def distance_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 500):
            raise ValueError("距離範圍需在 1～500 km 之間")
        return v

    @field_validator("preferred_genders")
    @classmethod
    def valid_genders(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            invalid = set(v) - VALID_GENDERS
            if invalid:
                raise ValueError(f"無效的性別偏好值: {invalid}")
        return v


class PreferenceOut(BaseModel):
    id: int
    user_id: int
    min_age: int
    max_age: int
    max_distance_km: int
    preferred_genders: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

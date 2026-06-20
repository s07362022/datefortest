import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class GenderEnum(str, enum.Enum):
    woman = "woman"
    man = "man"
    non_binary = "non_binary"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class InterestedInEnum(str, enum.Enum):
    women = "women"
    men = "men"
    non_binary = "non_binary"
    everyone = "everyone"


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_profile_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    gender: Mapped[GenderEnum | None] = mapped_column(Enum(GenderEnum), nullable=True)
    interested_in: Mapped[InterestedInEnum | None] = mapped_column(Enum(InterestedInEnum), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")
    profile_tags: Mapped[list["ProfileTag"]] = relationship("ProfileTag", back_populates="profile", cascade="all, delete-orphan")

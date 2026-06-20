from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Preference(Base):
    __tablename__ = "preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_preference_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    min_age: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    max_age: Mapped[int] = mapped_column(Integer, default=99, nullable=False)
    max_distance_km: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    # Stored as comma-separated string for SQLite compat; service layer handles conversion
    preferred_genders: Mapped[str] = mapped_column(String(100), default="everyone", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="preferences")

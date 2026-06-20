from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    profile_tags: Mapped[list["ProfileTag"]] = relationship("ProfileTag", back_populates="tag")


class ProfileTag(Base):
    __tablename__ = "profile_tags"
    __table_args__ = (UniqueConstraint("profile_id", "tag_id", name="uq_profile_tag"),)

    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="profile_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="profile_tags")

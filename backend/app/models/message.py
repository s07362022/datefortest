from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Message(Base):
    """A chat message between two matched users."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    match: Mapped["Match"] = relationship("Match")
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])

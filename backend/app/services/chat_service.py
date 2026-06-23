"""WebSocket connection manager and message service for Phase 4 chat."""

from typing import Optional
from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.message import Message


# ── Connection Manager ────────────────────────────────────────────────────────

class ConnectionManager:
    """Manages active WebSocket connections per match room."""

    def __init__(self) -> None:
        # match_id → list of active WebSocket connections
        self._rooms: dict[int, list[WebSocket]] = {}

    async def connect(self, match_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms.setdefault(match_id, []).append(ws)

    def disconnect(self, match_id: int, ws: WebSocket) -> None:
        room = self._rooms.get(match_id, [])
        if ws in room:
            room.remove(ws)
        if not room:
            self._rooms.pop(match_id, None)

    async def broadcast(self, match_id: int, payload: dict, exclude: Optional[WebSocket] = None) -> None:
        """Send JSON payload to all connections in a room except the sender."""
        import json
        for ws in list(self._rooms.get(match_id, [])):
            if ws is not exclude:
                try:
                    await ws.send_text(json.dumps(payload, ensure_ascii=False))
                except Exception:
                    self.disconnect(match_id, ws)

    async def send_to(self, ws: WebSocket, payload: dict) -> None:
        """Send JSON payload to a single WebSocket."""
        import json
        try:
            await ws.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass


# Singleton instance used by the router
manager = ConnectionManager()


# ── Auth helper ───────────────────────────────────────────────────────────────

def resolve_match_member(db: Session, match_id: int, user_id: int) -> Match:
    """Return the Match if user is a member and it is active, else raise ValueError."""
    match = db.get(Match, match_id)
    if not match or not match.is_active:
        raise ValueError("MATCH_NOT_FOUND")
    if match.user1_id != user_id and match.user2_id != user_id:
        raise ValueError("NOT_MATCH_MEMBER")
    return match


# ── Message CRUD ──────────────────────────────────────────────────────────────

def save_message(db: Session, match_id: int, sender_id: int, content: str) -> Message:
    """Persist a new message and return it."""
    msg = Message(match_id=match_id, sender_id=sender_id, content=content.strip())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, match_id: int, limit: int = 50, before_id: Optional[int] = None) -> list[Message]:
    """Return messages for a match, newest first, with cursor pagination."""
    q = db.query(Message).filter(Message.match_id == match_id)
    if before_id:
        q = q.filter(Message.id < before_id)
    return q.order_by(Message.created_at.desc()).limit(limit).all()


def mark_read(db: Session, match_id: int, reader_id: int) -> int:
    """Mark all unread messages in a match as read (where sender != reader).

    Returns the number of messages updated.
    """
    updated = (
        db.query(Message)
        .filter(
            Message.match_id == match_id,
            Message.sender_id != reader_id,
            Message.is_read == False,
        )
        .update({"is_read": True})
    )
    db.commit()
    return updated

"""Phase 4: REST endpoints for chat history and read-marking.

WebSocket endpoint lives in app/api/ws.py to keep routing clean.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.message import MessageListResponse, MessageOut, ReadResponse
from app.services.chat_service import get_messages, mark_read, resolve_match_member

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/{match_id}", response_model=MessageListResponse)
def list_messages(
    match_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    before_id: Optional[int] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return chat history for a match, newest first.

    Use before_id as a cursor for pagination (pass the smallest id from
    the previous page to fetch older messages).
    """
    try:
        resolve_match_member(db, match_id, current_user.id)
    except ValueError as e:
        code = str(e)
        raise HTTPException(status_code=404 if "NOT_FOUND" in code else 403,
                            detail={"code": code, "message": "無法存取此對話"})

    msgs = get_messages(db, match_id, limit=limit, before_id=before_id)
    next_cursor = msgs[-1].id if len(msgs) == limit else None
    return MessageListResponse(
        items=[MessageOut.model_validate(m) for m in msgs],
        next_cursor=next_cursor,
    )


@router.put("/{match_id}/read", response_model=ReadResponse)
def read_messages(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all unread messages from the other party as read."""
    try:
        resolve_match_member(db, match_id, current_user.id)
    except ValueError as e:
        code = str(e)
        raise HTTPException(status_code=404 if "NOT_FOUND" in code else 403,
                            detail={"code": code, "message": "無法存取此對話"})

    count = mark_read(db, match_id, current_user.id)
    return ReadResponse(marked_read=count)

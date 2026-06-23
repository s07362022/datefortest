"""Phase 4: WebSocket chat endpoint.

URL: ws://localhost:8000/ws/chat/{match_id}?token=<JWT>

Authentication via query-string token because browser WebSocket API
does not support custom headers.
"""

import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.services.chat_service import (
    manager,
    resolve_match_member,
    save_message,
)

ws_router = APIRouter()


@ws_router.websocket("/ws/chat/{match_id}")
async def chat_ws(
    match_id: int,
    websocket: WebSocket,
    token: str = "",
    db: Session = Depends(get_db),
):
    """Real-time chat WebSocket for a matched pair.

    Protocol:
    - Client connects with ?token=<JWT>
    - Client sends: {"content": "Hello!"}
    - Server broadcasts to all room members:
        {"event": "message", "id": 1, "sender_id": 2,
         "content": "Hello!", "created_at": "..."}
    - On auth / match error, server sends error JSON then closes.
    """
    # ── 1. Authenticate ───────────────────────────────────────────────────────
    try:
        payload = decode_access_token(token)
        user_id: int | None = payload.get("user_id")
    except Exception:
        user_id = None

    if not user_id:
        await websocket.accept()
        await websocket.send_text(
            json.dumps({"event": "error", "code": "UNAUTHORIZED", "message": "Token 無效"})
        )
        await websocket.close(code=4001)
        return

    # ── 2. Check match membership ─────────────────────────────────────────────
    try:
        resolve_match_member(db, match_id, user_id)
    except ValueError as exc:
        await websocket.accept()
        await websocket.send_text(
            json.dumps({"event": "error", "code": str(exc), "message": "無法存取此對話"})
        )
        await websocket.close(code=4003)
        return

    # ── 3. Main message loop ──────────────────────────────────────────────────
    await manager.connect(match_id, websocket)
    await manager.send_to(websocket, {"event": "connected", "match_id": match_id, "user_id": user_id})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_to(websocket, {"event": "error", "code": "INVALID_JSON", "message": "訊息格式錯誤"})
                continue

            content = (data.get("content") or "").strip()
            if not content:
                await manager.send_to(websocket, {"event": "error", "code": "EMPTY_CONTENT", "message": "訊息不可為空"})
                continue

            if len(content) > 2000:
                await manager.send_to(websocket, {"event": "error", "code": "TOO_LONG", "message": "訊息不超過 2000 字"})
                continue

            msg = save_message(db, match_id, user_id, content)

            payload_out = {
                "event": "message",
                "id": msg.id,
                "match_id": match_id,
                "sender_id": user_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            await manager.send_to(websocket, payload_out)
            await manager.broadcast(match_id, payload_out, exclude=websocket)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(match_id, websocket)

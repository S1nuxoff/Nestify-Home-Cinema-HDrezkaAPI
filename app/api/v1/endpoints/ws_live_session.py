# app/api/v1/endpoints/ws_live_session.py

from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from app.core.global_state import live_session
from app.websockets.manager import ws_manager

router = APIRouter()


@router.websocket("/ws/live_session")
async def live_session_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    await websocket.send_json(live_session)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

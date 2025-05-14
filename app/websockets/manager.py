from typing import List
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):  # створюємо копію списку
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS] Dead socket, removing: {e}")
                self.active_connections.remove(connection)


ws_manager = WebSocketManager()

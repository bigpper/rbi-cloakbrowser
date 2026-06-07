from __future__ import annotations

import asyncio
import logging

import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, health, profiles, sessions
from app.services.cdp_service import CdpService
from app.services.manager_client import ManagerClient
from app.services.session_service import InMemorySessionStore, SessionService

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("rbi-gateway")


def create_app() -> FastAPI:
    app = FastAPI(title="RBI Gateway")
    origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    store = InMemorySessionStore()
    manager_client = ManagerClient(settings.manager_base_url, settings.cloak_manager_auth_token)
    cdp_service = CdpService()
    app.state.store = store
    app.state.manager_client = manager_client
    app.state.cdp_service = cdp_service
    app.state.session_service = SessionService(store, manager_client, cdp_service)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(sessions.router)
    app.include_router(profiles.router)
    return app


app = create_app()


@app.websocket("/viewer-ws/{viewer_token}")
async def viewer_ws(websocket: WebSocket, viewer_token: str):
    """Authenticate viewer token, then proxy noVNC frames to Manager VNC."""
    try:
        session = websocket.app.state.session_service.get_session_by_viewer_token(viewer_token)
    except PermissionError:
        await websocket.close(code=4401, reason="Invalid viewer token")
        return

    await websocket.accept(subprotocol="binary" if "binary" in websocket.scope.get("subprotocols", []) else None)

    manager_ws_url = (
        settings.manager_base_url.replace("http://", "ws://").replace("https://", "wss://")
        + f"/api/profiles/{session.manager_profile_id}/vnc"
    )
    headers = {"Authorization": f"Bearer {settings.cloak_manager_auth_token}"}

    try:
        async with websockets.connect(
            manager_ws_url,
            subprotocols=["binary"],
            additional_headers=headers,
            max_size=None,
            ping_interval=None,
            ping_timeout=None,
        ) as manager_ws:
            async def client_to_manager() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        if msg.get("bytes") is not None:
                            await manager_ws.send(msg["bytes"])
                        elif msg.get("text") is not None:
                            await manager_ws.send(msg["text"])
                except WebSocketDisconnect:
                    pass

            async def manager_to_client() -> None:
                async for msg in manager_ws:
                    if isinstance(msg, bytes):
                        await websocket.send_bytes(msg)
                    else:
                        await websocket.send_text(msg)

            tasks = [
                asyncio.create_task(client_to_manager()),
                asyncio.create_task(manager_to_client()),
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except Exception as exc:
        logger.warning("viewer websocket proxy failed for session %s: %s", session.id, type(exc).__name__)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

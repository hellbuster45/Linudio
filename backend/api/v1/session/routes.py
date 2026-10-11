import asyncio
import os
import signal
import threading

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Set by Linudio.bat. When on, the browser tab holds a WebSocket open to this server, and the
# server shuts itself down once the last tab has been gone for a few seconds. Off by default,
# so a normal `uvicorn main:app` is never stopped by the browser.
EXIT_ON_CLOSE = os.environ.get("LINUDIO_EXIT_ON_CLOSE") == "1"
# Long enough to ride out a page refresh or a dev-mode remount, short enough to feel immediate.
GRACE_SECONDS = 8
# If the graceful stop hangs (e.g. a model is mid-download), force it after this long.
FORCE_EXIT_SECONDS = 10

router = APIRouter(prefix="/session", tags=["Session"])

_connections = 0
_shutdown_task: asyncio.Task | None = None


def _stop_server():
    # uvicorn handles SIGINT/SIGTERM by finishing up and exiting; raising it ourselves is the
    # same as pressing Ctrl+C. The timer is the fallback if that doesn't finish.
    print("Browser tab closed - shutting down.", flush=True)
    timer = threading.Timer(FORCE_EXIT_SECONDS, lambda: os._exit(0))
    timer.daemon = True
    timer.start()
    signal.raise_signal(signal.SIGINT)


async def _shutdown_after_grace():
    await asyncio.sleep(GRACE_SECONDS)
    if _connections == 0:
        _stop_server()


@router.get("")
def session_info():
    return {"exit_on_close": EXIT_ON_CLOSE}


@router.websocket("/ws")
async def session_socket(websocket: WebSocket):
    global _connections, _shutdown_task
    await websocket.accept()
    _connections += 1
    if _shutdown_task:
        _shutdown_task.cancel()
        _shutdown_task = None
    try:
        while True:
            await websocket.receive_text()  # nothing is expected; this just waits for the tab to go away
    except WebSocketDisconnect:
        pass
    finally:
        _connections -= 1
        if EXIT_ON_CLOSE and _connections == 0:
            _shutdown_task = asyncio.create_task(_shutdown_after_grace())

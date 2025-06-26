"""
Tiny dispatcher: 3 lines + decorator.  Nothing else ever changes here.
"""
import importlib
import pkgutil
from typing import Awaitable, Callable, Dict, List

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope

Handler = Callable[[WebsocketEnvelope, "TransportConsumer"], Awaitable[List[WebsocketEnvelope]]]
_handlers: Dict[str, Handler] = {}  # kind → coroutine

_loaded = False


def _ensure_handlers_loaded() -> None:
    global _loaded
    if _loaded:
        return
    PACKAGE_PREFIX = "puzzles.socket.systems"
    # iterate over every .py in the "systems" package
    for mod_info in pkgutil.iter_modules(importlib.import_module(PACKAGE_PREFIX).__path__):
        if not mod_info.ispkg:
            importlib.import_module(f"{PACKAGE_PREFIX}.{mod_info.name}")
    _loaded = True


def command(kind: str) -> Callable[[Handler], Handler]:
    from puzzles.socket.transport.errors import recover_missing_attempt
    def decorator(fn: Handler) -> Handler:
        if kind in _handlers:
            raise RuntimeError(f"handler for {kind!r} already registered")
        _handlers[kind] = recover_missing_attempt(fn)
        return fn

    return decorator


async def route(cmd: WebsocketEnvelope, ctx) -> List[WebsocketEnvelope]:
    """
    Look up by envelope.kind and run the handler.
    Unknown kinds → empty list (caller may send EventError instead).
    """
    _ensure_handlers_loaded()
    handler = _handlers.get(cmd.payload.kind)
    if handler:
        return await handler(cmd, ctx)
    print("No handler for command:", cmd.kind)
    return []

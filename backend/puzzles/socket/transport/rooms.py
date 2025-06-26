import asyncio
from collections import defaultdict
from typing import DefaultDict, Set

import msgpack
from channels.layers import get_channel_layer

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope


class Room:
    """Async-safe membership set (no external deps)."""

    def __init__(self) -> None:
        self._members: Set[str] = set()
        self._lock = asyncio.Lock()

    async def add_user(self, channel: str) -> None:
        async with self._lock:
            self._members.add(channel)

    async def remove_user(self, channel: str) -> None:
        async with self._lock:
            self._members.remove(channel)

    async def discard(self, channel: str) -> None:
        async with self._lock:
            self._members.discard(channel)

    async def members(self) -> Set[str]:
        async with self._lock:
            return set(self._members)

    async def broadcast(self, envelope: WebsocketEnvelope, *, origin: str | None = None) -> None:
        """
        Send the same envelope to every channel in the room
        (except `origin`, if given). Always msgpack on the wire.
        """
        chan_layer = get_channel_layer()
        payload = msgpack.packb(envelope.model_dump(mode="json"), use_bin_type=True)
        for ch in await self.members():
            await chan_layer.send(ch, {
                "type": "room.send",
                "bytes": payload
            })


_rooms: DefaultDict[str, Room] = defaultdict(Room)


def get_room(name: str) -> Room:
    return _rooms[name]


def room_name(mode: str, attempt_id: str) -> str:
    return f"game:{mode}:{attempt_id}"

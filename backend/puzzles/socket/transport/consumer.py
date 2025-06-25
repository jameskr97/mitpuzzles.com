import asyncio, json, msgpack, time
from channels.generic.websocket import AsyncWebsocketConsumer
from pydantic_core import ValidationError

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.room_schema     import CommandJoin, CommandLeave
from protocol.generated.websocket.ping_schema     import CommandPing
from puzzles.socket.transport.rooms   import get_room
from puzzles.socket.transport.router  import route             # ← tiny dispatcher

PING_INTERVAL = 2
TIMEOUT_CODE  = 4008

class TransportConsumer(AsyncWebsocketConsumer):
    """
    1. accept / close
    2. decode Envelope (json or msgpack) → router
    3. handle join/leave at transport layer
    4. heartbeat (ping→pong watchdog)
    """

    # ---------- lifecycle ----------
    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        await self._leave_room()

    # ---------- websocket pump ----------
    async def receive(self, text_data=None, bytes_data=None):
        raw = text_data or bytes_data
        try:
            if text_data:
                env = WebsocketEnvelope.model_validate_json(raw)  # JSON
            else:
                env = WebsocketEnvelope.model_validate(msgpack.unpackb(raw, raw=False))  # msgpack
        except ValidationError as exc:
            print("Validaion error:", exc)
            return await self.close(4000)
        except Exception as exc:
            print("Error parsing envelope:", exc)
            return await self.close(4001)

        # fast transport-level commands
        if isinstance(env.payload, CommandJoin):
            return await self._join(env)
        if isinstance(env.payload, CommandLeave):
            return await self._leave_room()

        # everything else → router
        responses = await route(env, self)
        if responses:
            for ev in responses:
                await self._send(ev)
        return None

    # ---------- room helpers ----------
    async def _join(self, env: WebsocketEnvelope):
        cmd: CommandJoin = env.payload
        await self._leave_room()                           # leave old
        self._room = cmd.room
        await get_room(cmd.room).add(self.channel_name)

        # fabricates EventJoined via handler; but keep local state
        for ev in await route(env, self):
            await self._send(ev)

    async def _leave_room(self):
        if hasattr(self, "_room"):
            await get_room(self._room).discard(self.channel_name)
            del self._room

    # ---------- send ----------
    async def _send(self, env: WebsocketEnvelope):
        # always msgpack on the wire; switch to .model_dump_json() if you prefer JSON
        await self.send(
            bytes_data=msgpack.packb(env.model_dump(mode="json"), use_bin_type=True)
        )

    # - channel handlers -
    async def room_send(self, event):
        await self.send(bytes_data=event["bytes"])

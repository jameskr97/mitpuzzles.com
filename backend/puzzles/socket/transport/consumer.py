import logging

import msgpack
from channels.generic.websocket import AsyncWebsocketConsumer
from pydantic_core import ValidationError

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.room_schema import CommandJoin, CommandLeave
from puzzles.socket.transport.rooms import get_room
from puzzles.socket.transport.router import route  # ← tiny dispatcher

PING_INTERVAL = 2
TIMEOUT_CODE = 4008

logger = logging.getLogger(__name__)

class TransportConsumer(AsyncWebsocketConsumer):
    """
    1. accept / close
    2. decode Envelope (json or msgpack) → router
    3. handle join/leave at transport layer
    4. heartbeat (ping→pong watchdog)
    """

    # region lifecycle
    async def connect(self):
        logger.info("Websocket connection established: %s", self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        logger.info("Websocket connection closed: %s (code: %d)", self.channel_name, code)
        await self._leave_room()

    # endregion

    # region message pump
    async def receive(self, text_data=None, bytes_data=None):
        raw = text_data or bytes_data
        try:
            if text_data:
                logger.log(5, "Received text data: %s", raw)
                env = WebsocketEnvelope.model_validate_json(raw)  # JSON
            else:
                logger.log(5, "Received bytes data: %s", raw)
                env = WebsocketEnvelope.model_validate(msgpack.unpackb(raw, raw=False))  # msgpack
            logger.debug(f"Message received: {env}")
        except ValidationError as exc:
            logger.error("Validation error in envelope: %s", exc)
            return self.close(4000)
        except Exception as exc:
            logger.error("Failed to decode envelope: %s", exc)
            return self.close(4001)

        # fast transport-level commands
        if isinstance(env.payload, CommandJoin):
            return self._join(env)
        if isinstance(env.payload, CommandLeave):
            return self._leave_room()

        # everything else → router
        responses = await route(env, self)
        await self._dispatch(responses)
        return None

    async def _dispatch(self, item):
        """
        Recursively fan‑out whatever the handler returned.

        Handlers may legally return:
          * None
          * a single WebsocketEnvelope
          * an iterable (list/tuple) of WebsocketEnvelopes — possibly nested

        This helper flattens the structure and forwards every envelope to _send().
        """
        if item is None:
            return
        if isinstance(item, (list, tuple)):
            for sub in item:
                await self._dispatch(sub)
            return
        # single envelope
        await self._send(item)



    # endregion

    # region room helpers
    async def _join(self, env: WebsocketEnvelope):
        cmd: CommandJoin = env.payload
        await self._leave_room()
        self._room = cmd.room
        await get_room(cmd.room).add_user(self.channel_name)

        # fabricates EventJoined via handler; but keep local state
        for ev in await route(env, self):
            await self._send(ev)

    async def _leave_room(self):
        if hasattr(self, "_room"):
            await get_room(self._room).discard(self.channel_name)
            del self._room

    # endregion

    # region sender + channel handlers
    async def _send(self, env: WebsocketEnvelope):
        # always msgpack on the wire; switch to .model_dump_json() if you prefer JSON
       await self.send(
            bytes_data=msgpack.packb(env.model_dump(mode="json"), use_bin_type=True)
        )

    async def room_send(self, event):
        await self.send(bytes_data=event["bytes"])
    # endregion

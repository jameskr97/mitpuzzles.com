import time

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.ping_schema import (
    CommandPing, EventPong, EventPongPayload
)
from puzzles.socket.transport.router import command


@command("ping")
def handle_ping(env: WebsocketEnvelope, _ctx):
    cmd: CommandPing = CommandPing.model_validate(env.payload)  # typed by discriminator
    pong = EventPong(
        kind="pong",
        payload=EventPongPayload(
            client_ts=cmd.payload.client_ts,
            server_recv=int(time.time() * 1000),
        )
    )
    return [env.model_copy(update={"kind": "pong", "payload": pong})]

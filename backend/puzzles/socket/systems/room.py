from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.room_schema     import (
    CommandJoin, CommandLeave, EventJoined
)
from puzzles.socket.transport.rooms   import get_room
from puzzles.socket.transport.router  import command

@command("join")
async def handle_join(env: WebsocketEnvelope, ctx):
    cmd: CommandJoin = env.payload
    room = get_room(cmd.room)
    await room.add(ctx.channel_name)

    joined = EventJoined(kind="joined", room=cmd.room)
    return [env.model_copy(update={"kind": "joined", "payload": joined})]

@command("leave")
async def handle_leave(env: WebsocketEnvelope, ctx):
    cmd: CommandLeave = env.payload
    await get_room(cmd.room).discard(ctx.channel_name)
    return []                                      # no server echo needed

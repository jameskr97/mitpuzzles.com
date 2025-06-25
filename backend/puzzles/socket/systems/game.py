from channels.db import database_sync_to_async

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.game_schema import (
    EventState,
    CommandAction,
    CommandClear,
    CommandLoad,
    CommandRefresh,
    EventSubmitResult,
    CommandToggleTutorial,
)

from puzzles.models import Puzzle
from puzzles.socket.systems.identify import require_freeplay, require_prolific
from puzzles.socket.systems.session_manager import SESSIONS, EngineWrapper
from puzzles.socket.transport.rooms import room_name, get_room
from puzzles.socket.transport.router import command


def _make_state(env: WebsocketEnvelope, wrapper: EngineWrapper, sid: str):
    attempt = wrapper.storage  # now an instance, not a class
    puzzle = attempt.puzzle  # real Puzzle row
    engine = wrapper.engine

    return env.model_copy(
        update={
            "kind": "state",
            "payload": EventState(
                kind="state",
                session_id=str(sid),
                puzzle_type=puzzle.puzzle_type,
                rows=engine.rows,
                cols=engine.cols,
                board=engine.board_state,
                violations=[v.to_dict() for v in engine.validate()],
                solved=attempt.is_solved,
                **engine.serialize_gamedata(),
            ),
        }
    )


async def _broadcast_state(ctx, env: WebsocketEnvelope, wrapper: EngineWrapper, sid: str):
    """
    Helper to broadcast the current state to the room.
    """
    mode = ctx.scope["mode"]
    state_env = _make_state(env, wrapper, sid)
    room_id = room_name(mode, sid)
    await get_room(room_id).broadcast(state_env)


async def _broadcast_submit_result(ctx, env: WebsocketEnvelope, wrapper: EngineWrapper, sid: str):
    """
    Helper to broadcast the submit result to the room.
    """
    mode = ctx.scope["mode"]

    result_env = env.model_copy(
        update={
            "kind": "submit_result",
            "payload": EventSubmitResult(
                kind="submit_result",
                session_id=sid,
                solved=wrapper.storage.is_solved,
            ),
        }
    )
    room_id = room_name(mode, sid)
    await get_room(room_id).broadcast(result_env)


@command("load")
async def handle_load(env: WebsocketEnvelope, ctx):
    cmd: CommandLoad = env.payload
    visitor = ctx.scope["visitor_id"]
    mode = ctx.scope["mode"]

    # get EngineWrapper
    sid = await SESSIONS.load(visitor, cmd.puzzle_type, mode)
    wrapper = SESSIONS.get_wrapper(sid)

    # join room
    room_id = room_name(mode, sid)
    await get_room(room_id).add_user(ctx.channel_name)
    await _broadcast_state(ctx, env, wrapper, sid)

    return []

@command("resume")
async def handle_resume(env: WebsocketEnvelope, ctx):
    cmd: CommandResume = env.payload
    mode = ctx.scope["mode"]
    wrap = await SESSIONS.get_or_load_wrapper(cmd.session_id, mode)
    room_id = room_name(mode, cmd.session_id)
    await get_room(room_id).add_user(ctx.channel_name)
    await _broadcast_state(ctx, env, wrap, cmd.session_id)

@command("refresh")
async def handle_refresh(env: WebsocketEnvelope, ctx):
    """
    Replace the current board in this session with a fresh puzzle of the same
    type (optionally filtered by size/difficulty). The session/room/owner stay
    the same; only the underlying puzzle row changes.
    """
    cmd: CommandRefresh = env.payload
    mode = ctx.scope["mode"]
    await SESSIONS.get_or_load_wrapper(cmd.session_id, mode)
    wrap: EngineWrapper = await SESSIONS.refresh(cmd)

    state_env = _make_state(env, wrap, cmd.session_id)
    room_id = room_name(mode, cmd.session_id)
    await get_room(room_id).broadcast(state_env)


@command("action")
async def handle_action(env: WebsocketEnvelope, ctx):
    """
    Handle a user input event (click, drag, etc.) on the game board.
    """
    cmd: CommandAction = env.payload
    mode = ctx.scope["mode"]

    wrap = await SESSIONS.get_or_load_wrapper(cmd.session_id, mode)
    # 2 - do action
    if wrap.engine.handle_input_event(cmd.payload):
        await database_sync_to_async(wrap.sync_and_flush)()
        await _broadcast_state(ctx, env, wrap, cmd.session_id)


@command("clear")
async def handle_clear(env: WebsocketEnvelope, ctx):
    cmd: CommandClear = env.payload
    mode = ctx.scope["mode"]

    wrap = await SESSIONS.get_or_load_wrapper(cmd.session_id, mode)
    if wrap.engine.board_clear():
        await _broadcast_state(ctx, env, wrap, cmd.session_id)


@command("submit")
async def handle_submit(env: WebsocketEnvelope, ctx):
    """Handle a submission of the current board state."""
    cmd: CommandAction = env.payload
    wrap = SESSIONS.get_wrapper(cmd.session_id)
    if wrap is None:
        return

    solved = wrap.engine.is_solved()
    wrap.storage.is_solved = solved
    await database_sync_to_async(wrap.storage.save)()

    await _broadcast_submit_result(ctx, env, wrap, cmd.session_id)


@command("toggle_tutorial")
async def handle_toggle_tutorial(env: WebsocketEnvelope, ctx):
    cmd: CommandToggleTutorial = env.payload
    mode = ctx.scope["mode"]
    wrap = await SESSIONS.get_or_load_wrapper(cmd.session_id, mode)
    wrap.engine.tutorial_mode = cmd.enabled
    await _broadcast_state(ctx, env, wrap, cmd.session_id)

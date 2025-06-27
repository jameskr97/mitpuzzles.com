import logging

from django.utils import timezone

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.game_schema import (
    EventState,
    CommandAction,
    CommandClear,
    CommandLoad,
    CommandRefresh,
    EventSubmitResult,
    CommandToggleTutorial, CommandResume, CommandSubmit
)
from puzzles.socket.systems.session_manager import SESSIONS, EngineWrapper, AttemptMissingException
from puzzles.socket.transport.rooms import room_name, get_room
from puzzles.socket.transport.router import command

logger = logging.getLogger(__name__)


def _make_state(env: WebsocketEnvelope, wrapper: EngineWrapper, sid: str):
    attempt = wrapper.storage  # now an instance, not a class
    puzzle = attempt.puzzle  # real Puzzle row
    engine = wrapper.engine

    mutable_cells = sum(1 for cell in engine.get_immutable_cells() if cell == 0)
    mistake_count = engine.calculate_number_of_mistakes()

    payload = EventState(
        kind="state",
        attempt_id=str(sid),
        puzzle_type=puzzle.puzzle_type,  # always correct
        solved=attempt.is_solved,
        # points_earned=(mutable_cells - mistake_count) * 3,
        **engine.serialize_gamedata(),
    )

    try:
        payload.points_earned = max(0, (mutable_cells - mistake_count) * 3)
    except Exception as e:
        pass

    return env.model_copy(
        update={
            "kind": "state",
            "payload": payload
        }
    )


async def _broadcast_state(ctx, env: WebsocketEnvelope, wrapper: EngineWrapper, sid: str):
    """
    Helper to broadcast the current state to the room.
    """
    mode = ctx.scope["mode"]
    state_env = _make_state(env, wrapper, sid)
    room_id = room_name(mode, sid)
    logger.debug("Broadcasting state to room %s", room_id)
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
                attempt_id=sid,
                puzzle_type=wrapper.storage.puzzle.puzzle_type,
                solved=wrapper.storage.is_solved,
            ),
        }
    )
    room_id = room_name(mode, sid)
    await get_room(room_id).broadcast(result_env)
    return _make_state(env, wrapper, sid)


@command("load")
async def handle_load(env: WebsocketEnvelope, ctx):
    cmd: CommandLoad = env.payload
    visitor = ctx.scope["visitor"]
    mode = ctx.scope["mode"]

    # get EngineWrapper
    sid = await SESSIONS.load(str(visitor.id), cmd.puzzle_type, mode)
    wrapper = SESSIONS.get_wrapper(sid)

    room_id = room_name(mode, sid)
    logger.debug(f"Joining room {room_id}")
    await get_room(room_id).add_user(ctx.channel_name)
    await _broadcast_state(ctx, env, wrapper, sid)
    return [_make_state(env, wrapper, sid)]


@command("resume")
async def handle_resume(env: WebsocketEnvelope, ctx):
    cmd: CommandResume = env.payload
    mode = ctx.scope["mode"]
    visitor = ctx.scope["visitor"]

    try:
        # Try to load the requested wrapper from cache or DB
        wrap = await SESSIONS.get_or_load_wrapper(cmd.attempt_id, mode)
    except AttemptMissingException:
        # Session vanished → transparently start a new one
        sid = await SESSIONS.load(str(visitor.id), cmd.puzzle_type, mode, forced_id=cmd.attempt_id)
        wrap = SESSIONS.get_wrapper(sid)

    room_id = room_name(mode, cmd.attempt_id)
    await get_room(room_id).add_user(ctx.channel_name)
    await _broadcast_state(ctx, env, wrap, cmd.attempt_id)


@command("refresh")
async def handle_refresh(env: WebsocketEnvelope, ctx):
    """
    Replace the current board in this session with a fresh puzzle of the same
    type (optionally filtered by size/difficulty). The session/room/owner stay
    the same; only the underlying puzzle row changes.
    """
    cmd: CommandRefresh = env.payload
    mode = ctx.scope["mode"]
    visitor = ctx.scope["visitor"]

    await SESSIONS.get_or_load_wrapper(cmd.attempt_id, mode)
    wrap: EngineWrapper = await SESSIONS.refresh(cmd, str(visitor.id), mode)
    sid = str(wrap.storage.id)

    # leave original room if the attempt_id changed
    state_env = _make_state(env, wrap, sid)
    if sid != cmd.attempt_id:
        old_room_id = room_name(mode, cmd.attempt_id)
        await get_room(old_room_id).remove_user(ctx.channel_name)
        new_room_id = room_name(mode, sid)
        await get_room(new_room_id).add_user(ctx.channel_name)
        await get_room(new_room_id).broadcast(state_env)
    else:
        await _broadcast_state(ctx, env, wrap, sid)
    return [state_env]


@command("action")
async def handle_action(env: WebsocketEnvelope, ctx):
    """
    Handle a user input event (click, drag, etc.) on the game board.
    """
    cmd: CommandAction = env.payload
    mode = ctx.scope["mode"]
    visitor = ctx.scope["visitor"]

    # disallow actions on solved puzzles
    wrap = await SESSIONS.get_or_load_wrapper(cmd.attempt_id, mode)
    if wrap.storage.is_solved:
        return

    wrap = await SESSIONS.get_or_load_wrapper(cmd.attempt_id, mode)
    if wrap.engine.handle_input_event(cmd.payload):
        await wrap.sync_and_flush()
        await _broadcast_state(ctx, env, wrap, cmd.attempt_id)


@command("clear")
async def handle_clear(env: WebsocketEnvelope, ctx):
    cmd: CommandClear = env.payload
    mode = ctx.scope["mode"]

    wrap = await SESSIONS.get_or_load_wrapper(cmd.attempt_id, mode)
    if wrap.engine.board_clear():
        await _broadcast_state(ctx, env, wrap, cmd.attempt_id)
        return [_make_state(env, wrap, cmd.attempt_id)]


@command("submit")
async def handle_submit(env: WebsocketEnvelope, ctx):
    """Handle a submission of the current board state."""
    cmd: CommandSubmit = env.payload
    wrap = SESSIONS.get_wrapper(cmd.attempt_id)
    if wrap is None:
        raise ValueError("No wrapper found")
    solved = wrap.engine.is_solved()
    wrap.storage.is_solved = solved
    if solved:
        wrap.storage.completed_at = timezone.now()
        wrap.storage.completion_time_client_ms = int(cmd.client_duration)

    await wrap.sync_and_flush()
    await _broadcast_submit_result(ctx, env, wrap, cmd.attempt_id)


@command("toggle_tutorial")
async def handle_toggle_tutorial(env: WebsocketEnvelope, ctx):
    cmd: CommandToggleTutorial = env.payload
    mode = ctx.scope["mode"]
    wrap = await SESSIONS.get_or_load_wrapper(cmd.attempt_id, mode)
    wrap.engine.tutorial_mode = cmd.enabled

    # Always persist the flag if enabled and not solved, for all modes
    if cmd.enabled and not wrap.storage.is_solved:
        wrap.storage.used_tutorial = True
    await wrap.sync_and_flush()
    logger.info("Sending back state!")
    # await _broadcast_state(ctx, env, wrap, cmd.attempt_id)
    return [_make_state(env, wrap, cmd.attempt_id)]


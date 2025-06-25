from functools import wraps
import time

from channels.generic.websocket import AsyncWebsocketConsumer

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.identify_schema import CommandIdentify, EventError, EventIdentified
from puzzles.socket.transport.router import command

@command("identify")
async def handle_identify(env: WebsocketEnvelope, ctx: AsyncWebsocketConsumer):
    """
    One coroutine covers free-play **and** Prolific.
    - Free-play:   only {"mode":"freeplay"}
    - Prolific:    {"mode":"prolific", prolific_pid, study_id, prolific_sid}
    Optionally both can send `session_id` to resume.
    """
    cmd: CommandIdentify = env.payload
    scope = ctx.scope                     # channels connection scope

    # 0. Grab visitor_id from http-only cookie ----------------------
    visitor_id = scope["cookies"]["visitor_id"]
    if not visitor_id:
        # Very first request ever – create and set cookie via http view.
        return _error(env, "no_cookie", "visitor_id cookie missing")

    ctx.scope["mode"] = cmd.mode
    ctx.scope["visitor_id"] = visitor_id

    # 2. Respond that identity is confirmed; session handling comes later
    evt = EventIdentified(
        kind="identified",
        mode=cmd.mode,
        session_id='FAKE_SESSION_ID',  # placeholder, will be set later
        new=True,  # always new for now, no resume logic yet
    )
    return [env.model_copy(update={"kind": "identified", "payload": evt})]


    # 2. Resume or create session ----------------------------------
    # if cmd.session_id:
    #     wrap = SESSION.resume(cmd.session_id)
    #     if not wrap:
    #         return _error(env, "bad_session", "unknown session_id")
    #     sid, is_new = cmd.session_id, False
    # else:
    #     sid = SESSION.create(
    #         puzzle_type=puzzle_type,
    #         storage=storage_table,
    #         mode=cmd.mode,
    #         visitor_id=visitor_id,
    #     )
    #     is_new = True
    #
    # # 3. Success event ---------------------------------------------
    # evt = EventIdentified(kind="identified",
    #                       session_id=sid,
    #                       new=is_new,
    #                       mode=cmd.mode)
    # return [env.model_copy(update={"kind":"identified", "payload":evt})]


def _error(env, code, msg):
    err = EventError(kind="error", code=code, msg=msg)
    return [env.model_copy(update={"kind":"error", "payload":err})]

def _validate_prolific(cmd):
    # TODO: hit DB or call Prolific API – placeholder:
    print("_validate_prolific")
    if not (cmd.prolific_subject_id and cmd.prolific_study_id and cmd.prolific_session_id):
        return False, "missing prolific parameters"
    return True, ""

def _puzzle_for_study(study_id):
    # map study → fixed puzzle sequence
    print("new study puzzle")
    return "sudoku"

def _random_freeplay_puzzle():
    # quick placeholder
    print("freeplay placeholder")
    return "random"


# Decorators for mode checking
def require_mode(expected_mode):
    def decorator(func):
        @wraps(func)
        async def wrapper(env, ctx, *args, **kwargs):
            actual_mode = ctx.scope.get("mode")
            if actual_mode != expected_mode:
                return [env.model_copy(update={"kind": "error", "payload": EventError(
                    kind="error",
                    code="wrong_mode",
                    msg=f"Expected mode '{expected_mode}', but got '{actual_mode}'"
                )})]
            return await func(env, ctx, *args, **kwargs)
        return wrapper
    return decorator

require_freeplay = require_mode("freeplay")
require_prolific = require_mode("prolific")

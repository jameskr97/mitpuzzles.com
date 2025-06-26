import functools
import logging
import inspect

from channels.db import database_sync_to_async

from puzzles.socket.transport.rooms import room_name, get_room

logger = logging.getLogger(__name__)


def recover_missing_attempt(handler):
    """
    Wrap a command handler so that:
      • Free-play → recreate the row if it's gone.
      • Other modes → close the socket.
    """
    async def _call_and_maybe_await(*args, **kwargs):
        result = handler(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _wrapped(env, ctx, *a, **kw):
        from puzzles.socket.systems.session_manager import GAMEMODE_TO_ATTEMPT_TABLE_MAP, AttemptMissingException

        try:
            return await _call_and_maybe_await(env, ctx, *a, **kw)
        except AttemptMissingException as exc:
            mode = ctx.scope["mode"]

            # ---------- non-freeplay: shut the socket ----------
            if mode != "freeplay":
                logger.warning("Stale session %s for mode=%s → closing", exc.attempt_id, mode)
                await ctx.close(code=4401, reason="stale session")
                return

            # ---------- free-play recovery ----------
            visitor = ctx.scope.get("visitor")

            # ❶  determine puzzle_type (payload → DB)
            puzzle_type = getattr(env.payload, "puzzle_type", None)
            if not puzzle_type:
                attempt_model = GAMEMODE_TO_ATTEMPT_TABLE_MAP["freeplay"]
                try:
                    puzzle_type = await database_sync_to_async(
                        attempt_model.objects.values_list(
                            "puzzle__puzzle_type", flat=True
                        ).get
                    )(id=exc.attempt_id)
                except attempt_model.DoesNotExist:
                    logger.error("Cannot recreate attempt %s – row already purged", exc.attempt_id)
                    return

            # ❷  create replacement attempt
            from puzzles.socket.systems.session_manager import SESSIONS
            sid = await SESSIONS.load(visitor, puzzle_type, mode="freeplay", forced_id=exc.attempt_id)
            wrap = SESSIONS.get_wrapper(sid)

            # ❸  put this socket in the new room & broadcast state
            room_id = room_name("freeplay", sid)
            await get_room(room_id).add_user(ctx.channel_name)

            from puzzles.socket.systems.game import _broadcast_state, _make_state  # local import → no cycle
            await _broadcast_state(ctx, env, wrap, sid)
            return [_make_state(env, wrap, sid)]

    return _wrapped

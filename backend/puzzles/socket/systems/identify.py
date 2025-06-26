import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.identify_schema import CommandIdentify, EventIdentified, EventIdentifyError
from puzzles.socket.db import get_or_create_prolific_participation
from puzzles.socket.transport.router import command
from tracking.models import Visitor

logger = logging.getLogger(__name__)


def _gen_id_msg(env: WebsocketEnvelope, mode):
    return [env.model_copy(
        update={
            "kind": "identified",
            "payload": EventIdentified(
                kind="identified",
                mode=mode,
            )})]


@command("identify")
async def handle_identify(env: WebsocketEnvelope, ctx: AsyncWebsocketConsumer):
    """
    One coroutine covers free-play **and** Prolific.
    - Free-play:   only {"mode":"freeplay"}
    - Prolific:    {"mode":"prolific", prolific_pid, study_id, prolific_sid}
    Optionally both can send `session_id` to resume.
    """
    cmd: CommandIdentify = env.payload
    visitor_id = ctx.scope["cookies"]["visitor_id"]
    if not visitor_id:
        return _error(env, "no_cookie", "visitor_id cookie missing")

    ctx.scope["mode"] = cmd.mode
    ctx.scope["visitor"] = await database_sync_to_async(Visitor.objects.get)(id=visitor_id)

    if cmd.mode == "freeplay":
        logger.debug(f"Visitor {visitor_id} identified in freeplay mode")
        return _gen_id_msg(env, "freeplay")

    elif cmd.mode == "prolific":
        logger.debug(
            f"Visitor {visitor_id} identified in Prolific mode. [prolific_subject_id={cmd.prolific_subject_id}] [experiment_id={cmd.experiment_id}]")
        pp, created = get_or_create_prolific_participation(cmd.prolific_subject_id, cmd.prolific_study_id,
                                                           cmd.prolific_session_id)
        verb = "Created" if created else "Found"
        logger.debug(f"{verb} ProlificParticipation row: visitor={visitor_id}, experiment={cmd.experiment_id}")
        ctx.scope["prolific_participation"] = pp
        return _gen_id_msg(env, "prolific")
    return None


def _error(env, code, msg):
    err = EventIdentifyError(kind="error", code=code, msg=msg)
    return [env.model_copy(update={"kind": "error", "payload": err})]

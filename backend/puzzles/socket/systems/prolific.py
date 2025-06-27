import logging
from typing import List

from channels.db import database_sync_to_async
from django.utils import timezone, connection

from experiments.models import ProlificParticipation, ExperimentPuzzleAttempt
from protocol.generated.websocket.envelope_schema import WebsocketEnvelope
from protocol.generated.websocket.experiment_schema import EventExperimentState, CommandExperimentStep, \
    CommandExperimentNextTrial, CommandExperimentFinishTrial
from puzzles.socket.db import get_experiment_puzzle_attempts, create_attempts_and_update_pool
from puzzles.socket.transport.router import command

logger = logging.getLogger(__name__)

async def _send_experiment_state(env: WebsocketEnvelope, part: ProlificParticipation):
    existing: List[ExperimentPuzzleAttempt] = await get_experiment_puzzle_attempts(part)
    res = []
    for item in existing:
        res.append({
            "puzzle_id": str(item.puzzle_id),
            "session_id": str(item.id),
            "order": item.attempt_order,
            "is_finished": item.completed_at is not None,
        })
    boards = sorted(res, key=lambda x: x["order"])
    print(boards)

    # parts = ["consent", "instructions", "experiment", "survey"]
    # total_parts = 3 + 4
    # percent_complete = parts.index(part.current_step)

    return env.model_copy(update={
        "kind": "event_experiment_state",
        "boards": boards,
        "current_step": part.current_step or "consent",
        "payload": EventExperimentState(
            kind="event_experiment_state",
            boards=boards,
            participation_id=str(part.id),
            current_step=part.current_step or "consent",
            current_trial=part.current_trial,
            completed=part.completed,
            total_points=part.metadata["points_earned"] if part.metadata and "points_earned" in part.metadata else 0,

        )
    })


def mark_current_step(part: ProlificParticipation, step_name: str):
    part.current_step = step_name
    part.save()


#
# @command("experiment_init")
# def handle_experiment_init(env, ctx):
#     cmd: CommandExperimentInit = env.payload
#     participation = ctx.scope["prolific_participation"]
#
#     existing = get_experiment_puzzle_attempts(part)
#     if len(existing) == 4:
#         boards = sorted([{"puzzle_id": pid, "session_id": str(sid), "puzzle_type": ptype } for pid, sid, ptype in existing], key=lambda x: x["puzzle_id"])
#         x = [env.model_copy(update={
#             "kind": "event_experiment_state",
#             "boards": boards,
#             "current_step": part.current_step or "consent",
#             "payload": EventExperimentState(
#                 kind="event_experiment_state",
#                 boards=boards,
#                 participation_id=str(part.id),
#                 current_step=part.current_step or "consent",
#                 current_trial=part.current_trial,
#             )
#         })]
#         print(x)
#         return x
#     print("not doin that!")
#
#     boards = create_attempts_and_update_pool(part)
#
#     return [env.model_copy(update={
#         "kind": "event_experiment_state",
#         "boards": boards,
#         "current_step": part.current_step or "consent",
#         "current_trial": part.current_trial,
#     })]

@command("experiment_consent")
async def handle_consent(env: WebsocketEnvelope, ctx):
    pp: ProlificParticipation = ctx.scope["prolific_participation"]
    if pp.consented_at is None:
        pp.consented_at = timezone.now()
        pp.current_step = "instructions"
        await create_attempts_and_update_pool(pp)
    await database_sync_to_async(pp.save)()
    return [await _send_experiment_state(env, pp)]


@command("experiment_step")
async def handle_step(env, ctx):
    step: CommandExperimentStep = env.payload
    pp: ProlificParticipation = ctx.scope["prolific_participation"]
    pp.current_step = step.step_name
    await database_sync_to_async(pp.save)()


@command("experiment_finish_trial")
async def handle_finish_trial(env, ctx):
    payload: CommandExperimentFinishTrial = env.payload
    pp: ProlificParticipation = ctx.scope["prolific_participation"]
    pp.metadata["points_earned"] = payload.points
    att = await database_sync_to_async(pp.get_current_attempt)()
    if not att or att.completed_at:
        return
    att.completed_at = timezone.now()
    await att.asave(update_fields=["completed_at"])
    await pp.asave(update_fields=["metadata"])

@command("experiment_next_trial")
async def handle_next_trial(env, ctx):
    step: CommandExperimentNextTrial = env.payload
    pp: ProlificParticipation = ctx.scope["prolific_participation"]
    pp.current_trial += 1
    await pp.asave(update_fields=["current_trial"])
    return [await _send_experiment_state(env, pp)]

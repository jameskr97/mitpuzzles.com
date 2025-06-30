import random
from typing import Tuple

from channels.db import database_sync_to_async
from django.db import transaction
from django.db.models import Min, F
from django.utils import timezone

from experiments.models import ProlificParticipation, ExperimentPuzzlePool, ExperimentPuzzleAttempt
from puzzles.models import Puzzle


@database_sync_to_async
def get_prolific_participation(subject_id, study_id, session_id):
    return ProlificParticipation.objects.select_related("experiment").filter(
        prolific_subject_id=subject_id,
        prolific_study_id=study_id,
        prolific_session_id=session_id
    ).first()


@database_sync_to_async
def get_or_create_prolific_participation(visitor_id, experiment_id, subject_id, study_id, session_id) -> Tuple[
    ProlificParticipation, bool]:
    obj, created = ProlificParticipation.objects.select_related("experiment").get_or_create(
        visitor_id=visitor_id,
        experiment_id=experiment_id,
        prolific_subject_id=subject_id,
        prolific_study_id=study_id,
        prolific_session_id=session_id,
    )
    return obj, created


@database_sync_to_async
def create_attempts_and_update_pool(part):
    """
    Simplified puzzle distribution - gives the same 3 puzzles to everyone.

    Researchers can modify FIXED_PUZZLE_IDS to change which puzzles are distributed.

    aa836eec14430fe0
    482568dbc5f7b628
    5e9753f2c2618c33
    a05b4bcd4cbd270b
    3a14dcd67752b017
    8740b14434966ae4
    fd1a0334102ca2ef
    39a71cd2aae42f9c
    c027b23ca7779140
    2cff32b30eaf385a
    bcf02c353ab695c4
    4e879ebfbb8c613a
    """
    # Configuration: Researchers can modify these puzzle IDs
    FIXED_PUZZLE_HASHES = ["8740b14434966ae4", "fd1a0334102ca2ef", "39a71cd2aae42f9c"]
    random.shuffle(FIXED_PUZZLE_HASHES)

    # Keep transaction.atomic() for defensive programming and Django best practices
    with transaction.atomic():
        puzzle_objects = Puzzle.objects.filter(puzzle_hash__in=FIXED_PUZZLE_HASHES).all()
        attempts = ExperimentPuzzleAttempt.objects.bulk_create([
            ExperimentPuzzleAttempt(
                visitor_id=part.visitor.id,
                prolific_session=part,
                puzzle=puzzle,
                board_state=[],
                action_history=[],
                attempt_order=index
            ) for index, puzzle in enumerate(puzzle_objects)
        ])

        return [
            {"puzzle_id": a.puzzle_id, "session_id": str(a.id), "order": a.attempt_order}
            for a in attempts
        ]


@database_sync_to_async
def get_experiment_puzzle_attempts(prolific_session):
    return list(ExperimentPuzzleAttempt.objects.filter(prolific_session=prolific_session))


@database_sync_to_async
def _complete_current_attempt(pp: ProlificParticipation):
    """Mark the active attempt finished and bump trial counter."""
    att: ExperimentPuzzleAttempt = pp.get_current_attempt()
    if not att or att.completed_at:        # already done or nothing to mark
        return

    att.completed_at = timezone.now()
    att.save(update_fields=["completed_at"])

@database_sync_to_async
def _bump_points(pp: ProlificParticipation, pts: int):
    meta = dict(pp.metadata or {})
    meta["points_earned"] = pts
    pp.metadata = meta                         # *re-assign* the JSONField
    pp.save(update_fields=["metadata"])

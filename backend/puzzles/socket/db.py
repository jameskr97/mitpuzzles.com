import random
from typing import Tuple

from channels.db import database_sync_to_async
from django.db import transaction
from django.db.models import Min, F
from django.utils import timezone

from experiments.models import ProlificParticipation, ExperimentPuzzlePool, ExperimentPuzzleAttempt


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
    with transaction.atomic():
        qs = (ExperimentPuzzlePool.objects
              .select_for_update()
              .filter(experiment=part.experiment))

        min_served = qs.aggregate(Min("served"))["served__min"]
        bucket = list(qs.filter(served=min_served))
        if len(bucket) < 4:
            qs.update(served=0)
            bucket = list(qs.filter(served=0))

        chosen_rows = random.sample(bucket, k=4)
        ExperimentPuzzlePool.objects.filter(
            pk__in=[r.pk for r in chosen_rows]
        ).update(served=F("served") + 1)

        attempts = ExperimentPuzzleAttempt.objects.bulk_create([
            ExperimentPuzzleAttempt(
                visitor_id=part.visitor.id,
                prolific_session=part,
                puzzle=r.puzzle,
                board_state=[],
                action_history=[],
                attempt_order=index
            ) for index, r in enumerate(chosen_rows)
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

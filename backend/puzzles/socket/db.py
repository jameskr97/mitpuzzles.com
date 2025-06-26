import random

from channels.db import database_sync_to_async
from django.db import transaction
from django.db.models import Min

from experiments.models import ProlificParticipation, ExperimentPuzzlePool, ExperimentPuzzleAttempt


@database_sync_to_async
def get_prolific_participation(subject_id, study_id, session_id):
    return ProlificParticipation.objects.select_related("experiment").filter(
        prolific_subject_id=subject_id,
        prolific_study_id=study_id,
        prolific_session_id=session_id
    ).first()

@database_sync_to_async
def get_or_create_prolific_participation(subject_id, study_id, session_id):
    obj, created = ProlificParticipation.objects.select_related("experiment").get_or_create(
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
            ) for r in chosen_rows
        ])

        return [
            {"puzzle_id": a.puzzle_id, "session_id": str(a.id)}
            for a in attempts
        ]

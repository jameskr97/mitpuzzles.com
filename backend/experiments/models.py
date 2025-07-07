import uuid

from django.db import models

from puzzles.models import Puzzle
from puzzles.models.puzzle_attempt import AbstractPuzzleAttempt


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)

    # The experiment configuration
    config = models.JSONField(default=dict)
    # {
    #   "comprehension_check": {...},
    #   "trials": [...],
    #   "completion_code": "COMP123"
    # }
    is_active = models.BooleanField(default=True)
    completion_code = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name


class ProlificParticipation(models.Model):
    """Minimal tracking for Prolific participants"""
    # Prolific identifiers from URL (composite primary key)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    prolific_subject_id = models.CharField(max_length=100, db_index=True)
    prolific_study_id = models.CharField(max_length=100)
    prolific_session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Study Tracking
    visitor = models.ForeignKey('tracking.Visitor', on_delete=models.CASCADE)
    experiment_id = models.CharField(null=False)
    survey_response = models.JSONField(null=True, blank=True)

    experiment_data = models.JSONField(default=dict, blank=True)


class ExperimentPuzzlePool(models.Model):
    """One row per puzzle in THIS experiment."""
    experiment = models.ForeignKey(Experiment, on_delete=models.PROTECT)
    puzzle = models.ForeignKey(Puzzle, on_delete=models.PROTECT)
    served = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("experiment_id", "puzzle")


class ExperimentPuzzleAttempt(AbstractPuzzleAttempt):
    """
    Records each attempt a user makes at solving a puzzle in freeplay mode.
    This is used for puzzles that do not have a specific completion condition.
    """

    class Meta:
        verbose_name = "Prolific Puzzle Attempt"
        verbose_name_plural = "Prolific Puzzle Attempts"
    attempt_order = models.IntegerField(default=0)
    prolific_session = models.ForeignKey(ProlificParticipation, on_delete=models.CASCADE)

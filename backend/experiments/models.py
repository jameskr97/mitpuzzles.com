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
    prolific_id = models.CharField(max_length=100, db_index=True)
    study_id = models.CharField(max_length=100)
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Study Tracking
    consented_at = models.DateTimeField(null=True, blank=True)
    visitor = models.ForeignKey('tracking.Visitor', on_delete=models.CASCADE)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    survey_response = models.JSONField(null=True, blank=True)

    # Minimal progress tracking
    current_step = models.CharField(max_length=100)  # 0 = not started
    current_trial = models.IntegerField(default=0)  # 0 = not started
    completed = models.BooleanField(default=False)

class ExperimentPuzzleAttempt(AbstractPuzzleAttempt):
    """
    Records each attempt a user makes at solving a puzzle in freeplay mode.
    This is used for puzzles that do not have a specific completion condition.
    """
    class Meta:
        verbose_name = "Prolific Puzzle Attempt"
        verbose_name_plural = "Prolific Puzzle Attempts"

    # Additional fields specific to experiment mode can be added here if needed
    prolific_session = models.ForeignKey(ProlificParticipation, on_delete=models.CASCADE)



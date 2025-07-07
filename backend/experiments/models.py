import uuid

from django.db import models

from puzzles.models import Puzzle
from puzzles.models import AbstractPuzzleAttempt

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


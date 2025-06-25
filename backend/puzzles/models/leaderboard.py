from django.db import models

from puzzles.models import Puzzle



class PuzzleAttempt(models.Model):
    """
    Records each attempt a user makes at solving a puzzle.
    """

    class Meta:
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["visitor", "puzzle"]),
            models.Index(fields=["completed_at"]),
        ]

    completed_at = models.DateTimeField(auto_now_add=True)
    visitor = models.ForeignKey('tracking.Visitor', on_delete=models.CASCADE, related_name="puzzle_attempts")
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE, related_name="attempts")
    puzzle_duration = models.DurationField(null=True, blank=True)

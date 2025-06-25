import uuid

from django.db import models
from puzzles.models import Puzzle

from typing import Self


class AbstractPuzzleAttempt(models.Model):
    class Meta:
        abstract = True
        ordering = ["-created_at"]

    # metadata
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey('tracking.Visitor', on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_time_client = models.FloatField(null=True, blank=True)

    # puzzle data
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE, related_name="%(class)ss")
    board_state = models.JSONField()
    action_history = models.JSONField(default=list, blank=True)
    is_solved = models.BooleanField(default=False)

    @classmethod
    def get_or_create_for_actor(cls, visitor_id, puzzle_type: str) -> Self:
        """Creates a new puzzle session for the given actor and puzzle type."""
        # check if a session already exists for this visitor and puzzle type
        session =  cls.objects.select_related("puzzle").filter(puzzle__puzzle_type=puzzle_type, visitor_id=visitor_id).first()
        if session:
            return session

        # create a new session
        puzzle = Puzzle.get_random_puzzle(puzzle_type)
        session = cls.objects.create(
            visitor_id=visitor_id,
            puzzle=puzzle,
            board_state=[],
            action_history=[],
            is_solved=False,
        )
        return session


class FreeplayPuzzleAttempt(AbstractPuzzleAttempt):
    """
    Records each attempt a user makes at solving a puzzle in freeplay mode.
    This is used for puzzles that do not have a specific completion condition.
    """
    class Meta:
        verbose_name = "Freeplay Puzzle Attempt"
        verbose_name_plural = "Freeplay Puzzle Attempts"

    used_tutorial = models.BooleanField(default=False)

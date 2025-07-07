import uuid

from django.db import models
from typing import Self


class Puzzle(models.Model):
    """
    All pre-generated puzzles of all types will be stored in this table.
    """

    class Meta:
        ordering = ["-created_at"]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    puzzle_hash = models.CharField(max_length=64, unique=True)
    puzzle_type = models.CharField(max_length=32)  # minesweeper, sudoku, tents, battleship...
    puzzle_size = models.CharField(max_length=32)  # 5x5, 9x9, 10x10...
    puzzle_difficulty = models.CharField(max_length=32)  # easy, medium, hard...
    puzzle_data = models.JSONField()  # JSON Field for puzzle data, check serializers for structure

    def __str__(self):
        return f"Puzzle [{self.id:03d}, {self.puzzle_type}, {self.puzzle_difficulty}]"

    @classmethod
    def get_random_puzzle(cls, puzzle_type: str, puzzle_size: str = None, puzzle_difficulty: str = None):
        """
        Get a random puzzle of the specified type, size, and difficulty.
        :param puzzle_type: Type of the puzzle (e.g., "sudoku", "crossword").
        :param puzzle_size: Size of the puzzle (e.g., "9x9").
        :param puzzle_difficulty: Difficulty level of the puzzle (e.g., "easy", "medium", "hard").
        :return: A random Puzzle instance or None if no matching puzzle is found.
        """
        query = {"puzzle_type": puzzle_type}
        if puzzle_size:
            query["puzzle_size"] = puzzle_size
        else:
            all_sizes = cls.objects.filter(puzzle_type=puzzle_type).values_list("puzzle_size", flat=True).distinct()
            if all_sizes:
                # Parse sizes like "5x5" and get the smallest one based on first number
                smallest_size = min(all_sizes, key=lambda x: int(x.split("x")[0]))
                query["puzzle_size"] = smallest_size

        if puzzle_difficulty:
            query["puzzle_difficulty"] = puzzle_difficulty

        return cls.objects.filter(**query).order_by("?").first()


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
    completion_time_client_ms = models.FloatField(null=True, blank=True)

    # puzzle data
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE, related_name="%(class)ss")
    action_history = models.JSONField(default=list, blank=True)

    @classmethod
    def get_or_create_for_actor(cls, visitor_id, puzzle_type: str) -> Self:
        """Creates a new puzzle session for the given actor and puzzle type."""
        # check if a session already exists for this visitor and puzzle type
        session = cls.objects.select_related("puzzle").filter(puzzle__puzzle_type=puzzle_type, visitor_id=visitor_id,
                                                              is_solved=False).first()
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

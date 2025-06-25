import uuid

from django.db import models


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

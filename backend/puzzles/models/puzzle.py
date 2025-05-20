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
    puzzle_difficulty = models.CharField(max_length=32)  # 5x5easy, 9x9hard, 10x10easy...
    puzzle_data = models.JSONField()  # JSON Field for puzzle data, check serializers for structure

    def __str__(self):
        return f"Puzzle [{self.id:03d}, {self.puzzle_type}, {self.puzzle_difficulty}]"

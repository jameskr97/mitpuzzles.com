from django.db import models
from mitlogic import fields
from django.utils import timezone


class Puzzles(models.Model):
    """
    All pre-generated puzzles of all types will be stored in this table.
    """
    class Meta:
        db_table = "generated_puzzles"
        ordering = ["-created_at"]
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    puzzle_type = models.CharField(max_length=32) # minesweeper, sudoku, tents, battleship...
    puzzle_class = models.CharField(max_length=32) # 5x5easy, 9x9hard, 10x10easy...
    puzzle_data = models.JSONField()

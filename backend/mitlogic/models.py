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
    id = fields.ULIDField(primary_key=True, db_default=models.Func(function="gen_monotonic_ulid"))
    created_at = models.DateTimeField(db_default=timezone.now(), auto_now_add=True)
    updated_at = models.DateTimeField(db_default=timezone.now(), auto_now=True)
    puzzle_type = models.CharField(max_length=32) # minesweeper, sudoku, tents, battleship...
    puzzle_class = models.CharField(max_length=32) # 5x5easy, 9x9hard, 10x10easy...
    puzzle_data = models.JSONField()

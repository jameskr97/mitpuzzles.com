from django.db import models
from django.conf import settings


class Puzzles(models.Model):
    """
    All pre-generated puzzles of all types will be stored in this table.
    """

    class Meta:
        ordering = ["-created_at"]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # minesweeper, sudoku, tents, battleship...
    puzzle_type = models.CharField(max_length=32)
    puzzle_class = models.CharField(max_length=32)  # 5x5easy, 9x9hard, 10x10easy...
    # JSON Field for puzzle data, check serializers for structure
    puzzle_data = models.JSONField()

    def __str__(self):
        return f"Puzzle [{self.id:03d}, {self.puzzle_type}, {self.puzzle_class}]"


class GameRecording(models.Model):
    """
    A record of a game recording
    """

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recordings",
    )
    session_id = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    puzzle = models.ForeignKey("Puzzles", on_delete=models.CASCADE, related_name="recordings")
    data = models.JSONField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(models.Q(user__isnull=False) | models.Q(session_id__isnull=False)),
                name="user_or_session_required",
            )
        ]


class Feedback(models.Model):
    """
    A used submitted feedback string
    """

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback",
    )
    session_id = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    message = models.TextField()
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "feedback"
        constraints = [
            models.CheckConstraint(
                check=(models.Q(user__isnull=False) | models.Q(session_id__isnull=False)),
                name="feedback_user_or_session_required",
            )
        ]

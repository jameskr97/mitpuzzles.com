from django.db import models

from core.models import make_actor_mixin


class GameRecording(make_actor_mixin("recordings")):
    """
    A record of a game recording
    """
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    puzzle = models.ForeignKey("Puzzle", on_delete=models.CASCADE, related_name="recordings")
    data = models.JSONField()


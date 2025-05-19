from django.db import models
from django.db.models import Q

from accounts.models import User
from tracking.models import Visitor


class AbstractActorMixinBase(models.Model):
    """
    Abstract base class for models that have a related user or visitor
    """
    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=Q(user__isnull=False) | Q(visitor__isnull=False),
                name="actor_user_or_visitor_required"
            ),
            models.CheckConstraint(
                check=~(Q(user__isnull=False) & Q(visitor__isnull=False)),
                name="actor_only_one_of_user_or_visitor"
            ),
        ]

    def set_actor(self, actor):
        if isinstance(actor, User):
            self.user = actor
            self.visitor = None
        elif isinstance(actor, Visitor):
            self.visitor = actor
            self.user = None
        else:
            raise TypeError("actor must be User or Visitor")

    def get_actor(self):
        return self.user if self.user else self.visitor

    @classmethod
    def for_actor(cls, actor):
        if isinstance(actor, User):
            return cls.objects.filter(user=actor)
        elif isinstance(actor, Visitor):
            return cls.objects.filter(visitor=actor)
        raise TypeError("actor must be User or Visitor")


def make_actor_mixin(model_name: str):
    """
    Add the user + visitor fields to the model, along with constraints
    """
    class ActorMixin(AbstractActorMixinBase):
        user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name=f"{model_name}")
        visitor = models.ForeignKey(Visitor, null=True, blank=True, on_delete=models.SET_NULL, related_name=f"{model_name}")

        class Meta(AbstractActorMixinBase.Meta):
            abstract = True
    return ActorMixin


class Puzzles(models.Model):
    """
    All pre-generated puzzles of all types will be stored in this table.
    """

    class Meta:
        ordering = ["-created_at"]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    puzzle_type = models.CharField(max_length=32) # minesweeper, sudoku, tents, battleship...
    puzzle_class = models.CharField(max_length=32)  # 5x5easy, 9x9hard, 10x10easy...
    puzzle_data = models.JSONField()  # JSON Field for puzzle data, check serializers for structure

    def __str__(self):
        return f"Puzzle [{self.id:03d}, {self.puzzle_type}, {self.puzzle_class}]"


class GameRecording(make_actor_mixin("recordings")):
    """
    A record of a game recording
    """
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    puzzle = models.ForeignKey("Puzzles", on_delete=models.CASCADE, related_name="recordings")
    data = models.JSONField()


class Feedback(make_actor_mixin("feedback")):
    """
    A used submitted feedback string
    """
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "feedback"

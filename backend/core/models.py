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
                check=Q(user__isnull=False) | Q(visitor__isnull=False), name="actor_user_or_visitor_required"
            ),
            models.CheckConstraint(
                check=~(Q(user__isnull=False) & Q(visitor__isnull=False)), name="actor_only_one_of_user_or_visitor"
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
        visitor = models.ForeignKey(
            Visitor, null=True, blank=True, on_delete=models.SET_NULL, related_name=f"{model_name}"
        )

        class Meta(AbstractActorMixinBase.Meta):
            abstract = True

    return ActorMixin


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

from django.db import models
import uuid
from django.conf import settings
from django.db import models


class Visitor(models.Model):
    """
    Represents an anonymous visitor, tied to a long-lived HttpOnly cookie.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    last_seen = models.DateTimeField(auto_now=True)
    user_agent = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["last_seen"])]

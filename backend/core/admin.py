from django.contrib import admin
from django.contrib.sessions.models import Session

from core import models


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    actions = None


@admin.register(models.Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    actions = None
    list_display = ["id", "visitor", "message"]

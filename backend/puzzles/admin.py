from django.contrib import admin
from django.core.serializers import serialize
from django.db.models import JSONField, Count
from django.http import HttpResponse
from django.urls import path
from django_json_widget.widgets import JSONEditorWidget

from puzzles import models


@admin.register(models.Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    actions = None
    list_display = ["id", "created_at", "puzzle_type", "puzzle_size", "puzzle_difficulty", "recording_count"]
    list_filter = ["puzzle_type",  "puzzle_size", "puzzle_difficulty", "created_at"]
    formfield_overrides = {
        JSONField: {
            "widget": JSONEditorWidget(
                options={
                    "modes": ["view", "code"],
                    "mode": "view",
                }
            )
        },
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # note: "recordings" is the related name for GameRecording in the Puzzle model.
        #       It is defined as `related_name="recordings"` in the GameRecording model.
        return qs.annotate(_recording_count=Count("recordings"))

    @admin.display(ordering="_recording_count", description="# Recordings")
    def recording_count(self, obj):
        # this attribute comes from our annotation
        return getattr(obj, "_recording_count", 0)


from django.core.serializers import serialize
from django.http import HttpResponse
from django.urls import path
from django_json_widget.widgets import JSONEditorWidget
from django.db.models import JSONField, Count
from django.contrib import admin
from core import models

from django.contrib.sessions.models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    actions = None


@admin.register(models.Puzzles)
class PuzzleAdmin(admin.ModelAdmin):
    actions = None
    list_display = ["id", "created_at", "puzzle_type", "puzzle_class", "recording_count"]
    list_filter = ["puzzle_type", "puzzle_class", "created_at"]
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


@admin.register(models.GameRecording)
class GameRecordingAdmin(admin.ModelAdmin):
    actions = None
    change_list_template = "admin/core/gamerecording/change_list.html"
    list_display = ["id", "created_at", "user", "visitor_id", "puzzle__puzzle_type", "puzzle__puzzle_class"]
    list_filter = ["created_at", "puzzle__puzzle_class"]
    readonly_fields = ["created_at", "user", "visitor_id", "puzzle", "data"]

    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget(options={"modes": ["view", "code"], "mode": "view"})},
    }

    def get_urls(self):
        return [
            path("download/", self.admin_site.admin_view(self.export_view), name="core_gamerecording_export"),
            *super().get_urls(),
        ]

    def export_view(self, request):
        qs = self.get_queryset(request)
        json_data = serialize("json", qs, fields=("id", "created_at", "user", "visitor_id", "puzzle", "data"))
        response = HttpResponse(json_data, content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="game_recordings.json"'
        return response


@admin.register(models.Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    actions = None
    list_display = ["id", "visitor", "message"]

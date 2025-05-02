from rest_framework import serializers
import hashlib
import re
from core import models


class GameRecordingCreateSerializer(serializers.Serializer):
    puzzle_id = serializers.PrimaryKeyRelatedField(queryset=models.Puzzles.objects.all())
    data = serializers.JSONField(help_text="Recorded game data")
    timestamp = serializers.CharField()

    def create(self, validated_data):
        request = self.context["request"]
        kwargs = {
            "puzzle": validated_data["puzzle_id"],
            "data": validated_data["data"],
        }

        if request.user and request.user.is_authenticated:
            kwargs["user"] = request.user
        else:
            kwargs["visitor"] = request.visitor

        return models.GameRecording.objects.create(**kwargs)


class PuzzleQuerySerializer(serializers.Serializer):
    puzzle_type = serializers.CharField(required=True)
    variant = serializers.CharField(required=False, default="default")


class PuzzleBaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", min_value=5)
    rows = serializers.IntegerField(source="puzzle_data.rows", min_value=5)
    board_initial = serializers.CharField(source="puzzle_data.board_initial", help_text="Initial board state")
    board_solution_hash = serializers.SerializerMethodField(help_text="A SHA256 hash of the board solution")

    def get_board_solution_hash(self, obj):
        return hashlib.sha256(obj.puzzle_data["board_solution"].encode()).hexdigest()

class PuzzleTentsSerializer(PuzzleBaseSerializer):
    row_counts = serializers.ListField(source="puzzle_data.row_counts")
    col_counts = serializers.ListField(source="puzzle_data.col_counts")

class PuzzleKakurasuSerializer(PuzzleBaseSerializer):
    row_sum = serializers.ListField(source="puzzle_data.row_sum", help_text="List of row counts")
    col_sum = serializers.ListField(source="puzzle_data.col_sum", help_text="List of column counts")

class FeedbackSerializer(serializers.Serializer):
    message = serializers.CharField()
    metadata = serializers.JSONField()

    def create(self, validated_data):
        request = self.context["request"]

        kwargs = {
            "message": validated_data.get("message"),
            "metadata": validated_data.get("metadata")
        }

        if request.user and request.user.is_authenticated:
            kwargs["user"] = request.user
        else:
            kwargs["visitor"] = request.visitor

        return models.Feedback.objects.create(**kwargs)

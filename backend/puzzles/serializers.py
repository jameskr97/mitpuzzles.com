from rest_framework import serializers

from puzzles import models

import hashlib
import json

from puzzles.converters import game_state_to_string, get_translation_dict


class PuzzleDefinitionSolutionHashSerializer(serializers.Serializer):
    solution_hash = serializers.SerializerMethodField(help_text="SHA256 hash of the solution state")
    strict_solution_hash = serializers.SerializerMethodField(help_text="SHA256 hash of the solution state with strict values")

    def get_solution_hash(self, obj):

        translation = get_translation_dict(obj.puzzle_type)
        s = game_state_to_string(obj.puzzle_data["game_board"], translation)
        solution = "".join(map(str, s))
        # state_1d_list = [cell for row in game_board for cell in row]
        # encoded = json.dumps(state_1d_list, sort_keys=True).encode()
        # hash_value = hashlib.sha256(encoded).hexdigest()
        return solution

    def get_strict_solution_hash(self, obj):
        return "strict_solution_hash"

class PuzzleDefinitionSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Unique identifier for the puzzle")
    puzzle_type = serializers.CharField(help_text="Type of the puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows" ,help_text="Number of rows in the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", help_text="Number of columns in the puzzle")
    initial_state = serializers.SerializerMethodField(source='puzzle_data.game_state', help_text="Initial state of the puzzle")
    solutions = PuzzleDefinitionSolutionHashSerializer(source="*", help_text="Solution hashes for the puzzle")
    meta = serializers.SerializerMethodField(source="puzzle_data", help_text="Additional metadata for the puzzle")

    def get_initial_state(self, obj):
        state_2d = obj.puzzle_data["game_state"]
        state_1d_list = [cell for row in state_2d for cell in row]
        return state_1d_list

    def get_meta(self, obj):
        meta = obj.puzzle_data.copy()
        meta.pop("id")
        meta.pop("difficulty", None)
        meta.pop("idx", None)
        meta.pop('rows')
        meta.pop('cols')
        meta.pop('game_state', None)
        meta.pop('game_board', None)
        meta.pop('priority', None)
        meta.pop('size', None)


        key_conversion = {
            "row_tent_counts": "row_counts",
            "col_tent_counts": "col_counts",
            "row_sum": "row_sum",
            "col_sum": "col_sum",
        }


        return meta



class GameRecordingCreateSerializer(serializers.Serializer):
    puzzle_id = serializers.PrimaryKeyRelatedField(queryset=models.Puzzle.objects.all())
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

class PuzzleTentsSerializer(PuzzleBaseSerializer):
    row_counts = serializers.ListField(source="puzzle_data.row_counts")
    col_counts = serializers.ListField(source="puzzle_data.col_counts")

class PuzzleKakurasuSerializer(PuzzleBaseSerializer):
    row_sum = serializers.ListField(source="puzzle_data.row_sum", help_text="List of row counts")
    col_sum = serializers.ListField(source="puzzle_data.col_sum", help_text="List of column counts")


class LeaderboardEntrySerializer(serializers.Serializer):
    username = serializers.CharField(source="visitor.generated_username")
    duration_display = serializers.SerializerMethodField()
    rank = serializers.IntegerField()

    def get_duration_display(self, obj):
        if not obj.puzzle_duration:
            return None

        total_seconds = int(obj.puzzle_duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes}:{seconds:02d}" if minutes > 0 else f"{seconds}s"

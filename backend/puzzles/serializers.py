from rest_framework import serializers

from puzzles import models
from puzzles.encoder import PrecisePuzzleEncoder, PuzzleType


class PuzzleFreeplayAttemptSerializer(serializers.ModelSerializer):
    """Matches frontend PuzzleFreeplayAttemptPayload"""

    # Input fields matching frontend payload
    puzzle_id = serializers.IntegerField(write_only=True, help_text="ID of the associated puzzle")
    completion_time_client_ms = serializers.IntegerField(write_only=True,
                                                         help_text="Duration of the attempt in milliseconds")

    # Output fields for read operations
    puzzle = serializers.PrimaryKeyRelatedField(read_only=True)
    duration_ms = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.FreeplayPuzzleAttempt
        fields = [
            'id', 'visitor_id', 'puzzle', 'completed_at', 'duration_ms', 'action_history',
            'puzzle_id', 'completion_time_client_ms'
        ]
        read_only_fields = ['id', 'visitor_id', 'puzzle', 'duration_ms']

    def create(self, validated_data):
        # Extract and convert input fields
        puzzle_id = validated_data.pop('puzzle_id')
        completion_time_client_ms = validated_data.pop('completion_time_client_ms')

        # Get the puzzle instance
        try:
            puzzle = models.Puzzle.objects.get(id=puzzle_id)
        except models.Puzzle.DoesNotExist:
            raise serializers.ValidationError({"puzzle_id": "Puzzle not found"})

        # Get visitor from request
        request = self.context.get('request')
        if not hasattr(request, 'visitor') or request.visitor is None:
            raise serializers.ValidationError({"visitor": "Visitor not found in request context"})

        # Create the instance with correct field names
        return models.FreeplayPuzzleAttempt.objects.create(
            puzzle=puzzle,
            visitor=request.visitor,
            completion_time_client_ms=completion_time_client_ms,
            **validated_data
        )


class PuzzleDefinitionSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Unique identifier for the puzzle")
    puzzle_type = serializers.CharField(help_text="Type of the puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows", help_text="Number of rows in the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", help_text="Number of columns in the puzzle")
    initial_state = serializers.JSONField(source='puzzle_data.game_state', help_text="Initial state of the puzzle")
    solution_hash = serializers.SerializerMethodField(help_text="Solution hashes for the puzzle")
    meta = serializers.SerializerMethodField(source="puzzle_data", help_text="Additional metadata for the puzzle")

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

        return meta

    def get_solution_hash(self, obj) -> str:
        """Generate non-strict solution hash."""
        puzzle_type = PuzzleType(obj.puzzle_type)
        encoder = PrecisePuzzleEncoder(puzzle_type)

        return encoder.create_run_length_encoding(
            board=obj.puzzle_data["game_board"],
            puzzle_id=str(obj.id)
        )


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

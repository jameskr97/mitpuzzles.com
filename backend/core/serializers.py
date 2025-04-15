from rest_framework import serializers
import hashlib
import re
from core import models

class GameRecordingCreateSerializer(serializers.Serializer):
    puzzle_id = serializers.PrimaryKeyRelatedField(queryset=models.Puzzles.objects.all(), help_text="The ID of the puzzle being played")
    data = serializers.JSONField(help_text="Recorded game data")

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key

        return models.GameRecording.objects.create(
            user=user,
            session_id=session_id,
            puzzle=validated_data["puzzle_id"],
            data=validated_data["data"],
        )

class PuzzleQuerySerializer(serializers.Serializer):
    puzzle_type = serializers.CharField(max_length=20, required=True, help_text="The type of puzzle to retrieve (e.g., 'sudoku', 'minesweeper')")
    variant = serializers.CharField(max_length=20, required=True, help_text="The variant of the puzzle to retrieve (e.g., 'easy', 'medium', 'hard')")


class PuzzleMinesweeperSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", min_value=5, help_text="The number of columns in the minesweeper puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows", min_value=5, help_text="The number of rows in the minesweeper puzzle")
    board = serializers.SerializerMethodField(help_text="Board solution must only contain digits (0-8) and 'U'")
    solution_hash = serializers.CharField(source="puzzle_data.solution_hash", help_text="A SHA256 hash of the board solution")

    def get_board(self, obj):
        return re.sub(r"[A-Za-z]", "U", obj.puzzle_data["board"])


class PuzzleSudokuSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", min_value=9, help_text="The number of columns in the sudoku puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows", min_value=9, help_text="The number of rows in the sudoku puzzle")
    board = serializers.CharField(source="puzzle_data.board", help_text="The board solution must only contain digits (1-9) and '-'")
    solution_hash = serializers.SerializerMethodField(help_text="Get the hash of the solution")

    def get_solution_hash(self, obj):
        return hashlib.sha256(obj.puzzle_data["solution"].encode()).hexdigest()



class PuzzleTentsSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", min_value=5, help_text="The number of columns in the tents puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows", min_value=5, help_text="The number of rows in the tents puzzle")
    trees = serializers.CharField(source="puzzle_data.trees", help_text="The board solution must only contain digits (0-8) and 'U'")
    row_counts = serializers.ListField(source="puzzle_data.row_counts", help_text="List of row counts")
    col_counts = serializers.ListField(source="puzzle_data.col_counts", help_text="List of column counts")
    solution_hash = serializers.SerializerMethodField(help_text="A SHA256 hash of the board solution")

    def get_solution_hash(self, obj):
        return hashlib.sha256(obj.puzzle_data["tents"].encode()).hexdigest()


class PuzzleKakurasuSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", min_value=5, help_text="The number of columns in the tents puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows", min_value=5, help_text="The number of rows in the tents puzzle")
    row_sum = serializers.ListField(source="puzzle_data.row_sum", help_text="List of row counts")
    col_sum = serializers.ListField(source="puzzle_data.col_sum", help_text="List of column counts")
    solution_hash = serializers.SerializerMethodField(help_text="A SHA256 hash of the board solution")

    def get_solution_hash(self, obj):
        return hashlib.sha256(obj.puzzle_data["cells_black"].encode()).hexdigest()


class PuzzleLightupSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source="puzzle_data.cols", min_value=5, help_text="The number of columns in the  puzzle")
    rows = serializers.IntegerField(source="puzzle_data.rows", min_value=5, help_text="The number of rows in the tents puzzle")
    board = serializers.CharField(source="puzzle_data.board", help_text="List of column counts")
    solution_hash = serializers.SerializerMethodField(help_text="A SHA256 hash of the board solution")

    def get_solution_hash(self, obj):
        return hashlib.sha256(obj.puzzle_data["solution"].encode()).hexdigest()

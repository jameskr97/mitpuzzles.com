from rest_framework import serializers
import hashlib
import re


class PuzzleQuerySerializer(serializers.Serializer):
    puzzle_type = serializers.CharField(max_length=20, required=True, help_text="The type of puzzle to retrieve (e.g., 'sudoku', 'minesweeper')")
    variant = serializers.CharField(max_length=20, required=True, help_text="The variant of the puzzle to retrieve (e.g., 'easy', 'medium', 'hard')")

class PuzzleMinesweeperSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source='puzzle_data.cols', min_value=5, help_text="The number of columns in the minesweeper puzzle")
    rows = serializers.IntegerField(source='puzzle_data.rows', min_value=5, help_text="The number of rows in the minesweeper puzzle")
    board = serializers.SerializerMethodField(help_text="Board solution must only contain digits (0-8) and 'U'")
    solution_hash = serializers.CharField(source='puzzle_data.solution_hash', help_text="A SHA256 hash of the board solution")

    def get_board(self, obj):
        return re.sub(r'[A-Za-z]', 'U', obj.puzzle_data["board"])

class PuzzleSudokuSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source='puzzle_data.cols', min_value=9, help_text="The number of columns in the sudoku puzzle")
    rows = serializers.IntegerField(source='puzzle_data.rows', min_value=9, help_text="The number of rows in the sudoku puzzle")
    board = serializers.CharField(source='puzzle_data.board', help_text="The board solution must only contain digits (1-9) and '-'")

class PuzzleTentsSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source='puzzle_data.cols', min_value=5, help_text="The number of columns in the tents puzzle")
    rows = serializers.IntegerField(source='puzzle_data.rows', min_value=5, help_text="The number of rows in the tents puzzle")
    trees = serializers.CharField(source='puzzle_data.trees', help_text="The board solution must only contain digits (0-8) and 'U'")
    row_counts = serializers.ListField(source='puzzle_data.row_counts', help_text="List of row counts")
    col_counts = serializers.ListField(source='puzzle_data.col_counts', help_text="List of column counts")
    solution_hash = serializers.SerializerMethodField(help_text="A SHA256 hash of the board solution")

    def get_solution_hash(self, obj):
        return hashlib.sha256(obj.puzzle_data["tents"].encode()).hexdigest()
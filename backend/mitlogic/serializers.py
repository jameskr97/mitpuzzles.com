from rest_framework import serializers
import re


class PuzzleMinesweeperSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Unique identifier for the puzzle")
    cols = serializers.IntegerField(source='puzzle_data.cols', min_value=5, help_text="The number of columns in the minesweeper puzzle")
    rows = serializers.IntegerField(source='puzzle_data.rows', min_value=5, help_text="The number of rows in the minesweeper puzzle")
    board = serializers.SerializerMethodField(help_text="Board solution must only contain digits (0-8) and 'U'")

    def get_board(self, obj):
        return re.sub(r'[A-Za-z]', 'U', obj.puzzle_data["board_solution"])


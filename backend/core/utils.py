from rest_framework.response import Response
from . import serializers

def get_puzzle_serializer(puzzle_type):
    serializers_map = {
        "sudoku": serializers.PuzzleSudokuSerializer,
        "minesweeper": serializers.PuzzleMinesweeperSerializer,
        "tents": serializers.PuzzleTentsSerializer,
        "kakurasu": serializers.PuzzleKakurasuSerializer,
        "lightup": serializers.PuzzleLightupSerializer,
    }
    serializer_class = serializers_map.get(puzzle_type)
    if serializer_class is None:
        return Response({"error": "Invalid puzzle type"}, status=400)
    return serializer_class
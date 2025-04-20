from rest_framework.response import Response
from django.core.signing import TimestampSigner
from . import serializers
import time


def get_puzzle_serializer(puzzle_type):
    serializers_map = {
        "sudoku": serializers.PuzzleBaseSerializer,
        "minesweeper": serializers.PuzzleBaseSerializer,
        "lightup": serializers.PuzzleBaseSerializer,
        "tents": serializers.PuzzleTentsSerializer,
        "kakurasu": serializers.PuzzleKakurasuSerializer,
    }
    serializer_class = serializers_map.get(puzzle_type)
    if serializer_class is None:
        return Response({"error": "Invalid puzzle type"}, status=400)
    return serializer_class


def get_signed_timestamp():
    current_time = str(int(time.time()))
    return TimestampSigner().sign(current_time)

from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response
from mitlogic import models
from mitlogic import serializers
import re

from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def get_random_puzzle(request):
    query = serializers.PuzzleQuerySerializer(data=request.query_params)
    if not query.is_valid():
        return Response(query.errors, status=400)
    puzzle_type = query.validated_data["puzzle_type"]
    variant = query.validated_data["variant"]

    res = models.Puzzles.objects.filter(puzzle_type=puzzle_type).order_by("?").first()
    if res is None:
        return Response({"error": "No puzzles found"}, status=404)

    serializers_map = {
        "sudoku": serializers.PuzzleSudokuSerializer,
        "minesweeper": serializers.PuzzleMinesweeperSerializer,
        "tents": serializers.PuzzleTentsSerializer,
        "kakurasu": serializers.PuzzleKakurasuSerializer,
        "lightup": serializers.PuzzleLightupSerializer,
    }

    serializer_class = serializers_map.get(
        puzzle_type, lambda _: Response({"error": "Invalid puzzle type"}, status=400)
    )
    serializer = serializer_class(res)
    if isinstance(serializer, Response):
        return serializer

    return Response(serializer.data)


@api_view(["GET"])
def get_random_puzzle_ms(request):
    x = models.Puzzles.objects.order_by("?").first()
    serialized = serializers.PuzzleMinesweeperSerializer(x)
    return Response(serialized.data)


@api_view(["GET"])
def get_random_puzzle_sudoku(request):
    x = models.Puzzles.objects.filter(puzzle_type="sudoku").order_by("?").first()
    serialized = serializers.PuzzleSudokuSerializer(x)
    return Response(serialized.data)


from .config import generate_settings_etag, get_game_settings


@etag(generate_settings_etag)
@api_view(["GET"])
def game_settings_view(request):
    return Response(get_game_settings())

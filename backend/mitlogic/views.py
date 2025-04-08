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
    if puzzle_type == "sudoku":
        res = models.Puzzles.objects.filter(puzzle_type="sudoku").order_by("?").first()
        serialized = serializers.PuzzleSudokuSerializer(res)
    elif puzzle_type == "minesweeper":
        res = models.Puzzles.objects.filter(puzzle_type="minesweeper").order_by("?").first()
        serialized = serializers.PuzzleMinesweeperSerializer(res)
    elif puzzle_type == "tents":
        res = models.Puzzles.objects.filter(puzzle_type="tents").order_by("?").first()
        serialized = serializers.PuzzleTentsSerializer(res)
    else:
        return Response({"error": "Invalid puzzle type"}, status=400)

    if res is None:
        return Response({"error": "No puzzles found"}, status=404)

    return Response(serialized.data)


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

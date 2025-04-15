from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from . import models, serializers, utils


@api_view(["POST"])
def submit_game_recording(request):
    serializer = serializers.GameRecordingCreateSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        recording = serializer.save()
        return Response({"id": recording.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def unsolved_puzzle_count(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key

    if not user and not session_id:
        return Response({"error": "Session ID not found."}, status=400)

    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list("puzzle_id", flat=True)

    count = models.Puzzles.objects.exclude(id__in=recorded_ids).count()
    return Response({"unsolved_count": count})


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

    serializer_class = utils.get_puzzle_serializer(puzzle_type)
    if isinstance(serializer_class, Response):
        return serializer_class

    return Response(serializer_class(res).data)


@api_view(["GET"])
def get_unsolved_puzzle(request):
    # Get the user or session ID from the request
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key
    if not user and not session_id:
        return Response({"error": "Session ID not found."}, status=400)

    # Check for unsolved puzzles of the given user or session
    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list("puzzle_id", flat=True)

    # Get a random unsolved puzzle
    puzzle = models.Puzzles.objects.exclude(id__in=recorded_ids).order_by("?").first()
    if puzzle is None:
        return Response({"error": "No unsolved puzzles available"}, status=404)

    serializer_class = utils.get_puzzle_serializer(puzzle.puzzle_type)
    if isinstance(serializer_class, Response):
        return serializer_class
    return Response(serializer_class(puzzle).data)


from .config import generate_settings_etag, get_game_settings


@etag(generate_settings_etag)
@api_view(["GET"])
def game_settings_view(request):
    return Response(get_game_settings())


@api_view(["GET"])
def unsolved_puzzle_count(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key

    if not user and not session_id:
        return Response({"error": "Session ID not found."}, status=400)

    puzzle_type = request.query_params.get("puzzle_type", None)

    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list("puzzle_id", flat=True)

    queryset = models.Puzzles.objects.exclude(id__in=recorded_ids)
    if puzzle_type:
        queryset = queryset.filter(puzzle_type=puzzle_type)
    count = queryset.count()

    return Response({"unsolved_count": count})


@api_view(["GET"])
def get_unsolved_puzzle(request):
    user = request.user if request.user.is_authenticated else None
    session_id = request.session.session_key

    if not user and not session_id:
        return Response({"error": "Session ID not found."}, status=400)

    puzzle_type = request.query_params.get("puzzle_type", None)
    variant = request.query_params.get("variant", None)

    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list("puzzle_id", flat=True)

    queryset = models.Puzzles.objects.exclude(id__in=recorded_ids)
    if puzzle_type:
        queryset = queryset.filter(puzzle_type=puzzle_type)
    puzzle = queryset.order_by("?").first()

    if puzzle is None:
        return Response({"error": "No unsolved puzzles available"}, status=404)

    serializer_class = utils.get_puzzle_serializer(puzzle.puzzle_type)
    serializer = serializer_class(puzzle)
    if isinstance(serializer, Response):
        return serializer

    return Response(serializer.data)

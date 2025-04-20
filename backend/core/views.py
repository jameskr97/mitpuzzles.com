from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

from . import models, serializers, utils


class PuzzleBaseAPIView(APIView):
    exclude_solved = False  # default
    puzzle_type_required = True
    variant_required = True

    def get(self, request):
        query = serializers.PuzzleQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        puzzle_type = query.validated_data.get("puzzle_type")
        variant = query.validated_data.get("variant", None)

        user = request.user if request.user.is_authenticated else None
        session_id = None if request.user.is_authenticated else request.session.session_key

        queryset = models.Puzzles.objects.all()

        if puzzle_type:
            queryset = queryset.filter(puzzle_type=puzzle_type)
        # if variant:
        #     queryset = queryset.filter(puzzle_class=variant)

        if self.exclude_solved:
            recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list(
                "puzzle_id", flat=True
            )
            queryset = queryset.exclude(id__in=recorded_ids)

        puzzle = queryset.order_by("?").first()

        if puzzle is None:
            return Response(
                {"type": "empty_puzzle_set", "message": "No available puzzles."},
                status=status.HTTP_200_OK,
            )

        serializer_class = utils.get_puzzle_serializer(puzzle.puzzle_type)
        return Response(
            {
                "type": "Puzzle",
                "data": {
                    **serializer_class(puzzle).data,
                    "timestamp": utils.get_signed_timestamp(),
                },
            }
        )


class RandomPuzzleView(PuzzleBaseAPIView):
    exclude_solved = False


class UnsolvedPuzzleView(PuzzleBaseAPIView):
    exclude_solved = True


class FeedbackAPIView(APIView):
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = serializers.FeedbackSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def fetch_random_puzzle(user, session_id, puzzle_type, variant=None, exclude_solved=False):
    queryset = models.Puzzles.objects.filter(puzzle_type=puzzle_type)
    if variant:
        queryset = queryset.filter(variant=variant)

    if exclude_solved:
        solved_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list(
            "puzzle_id", flat=True
        )
        queryset = queryset.exclude(id__in=solved_ids)

    return queryset.order_by("?").first()


@api_view(["POST"])
def submit_game_recording(request):
    serializer = serializers.GameRecordingCreateSerializer(data=request.data, context={"request": request})
    # check if the user already has a recording for this puzzle
    user = request.user if request.user.is_authenticated else None
    session_id = None if request.user.is_authenticated else request.session.session_key
    existing_recording = models.GameRecording.objects.filter(
        puzzle_id=request.data.get("puzzle"),
        user=user,
        session_id=session_id,
    ).first()
    if existing_recording:
        return Response(
            {"error": "Recording already exists for this puzzle."},
            status=status.HTTP_409_CONFLICT,
        )

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

    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list(
        "puzzle_id", flat=True
    )

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
    serializer_class = utils.get_puzzle_serializer(puzzle_type)
    if isinstance(serializer_class, Response):
        return serializer_class

    return Response(serializer_class(res).data)


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

    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list(
        "puzzle_id", flat=True
    )

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

    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(session_id=session_id)).values_list(
        "puzzle_id", flat=True
    )

    queryset = models.Puzzles.objects.exclude(id__in=recorded_ids)
    if puzzle_type:
        queryset = queryset.filter(puzzle_type=puzzle_type)
    puzzle = queryset.order_by("?").first()
    if puzzle is None:
        return Response(
            {
                "code": "no_unsolved_puzzle_found",
                "details": "No unsolved puzzles available for the user or session.",
            }
        )

    serializer_class = utils.get_puzzle_serializer(puzzle.puzzle_type)
    serializer = serializer_class(puzzle)
    if isinstance(serializer, Response):
        return serializer

    return Response(serializer.data)


@api_view(["POST"])
def validate_signed_serve_time(request):
    """
    Validates the signed server time sent in the request.
    """
    from django.core.signing import Signer, BadSignature

    signed_time = request.data.get("signed_time")
    if not signed_time:
        return Response({"error": "No signed time provided."}, status=400)

    signer = Signer()
    try:
        original_time = signer.unsign(signed_time)
        return Response({"valid": True, "original_time": original_time})
    except BadSignature:
        return Response({"valid": False}, status=400)


@api_view(["GET"])
def my_view(request):
    print("Request Headers:")
    for key, value in request.META.items():
        if key.startswith("HTTP_"):
            print(f"{key}: {value}")
    return Response("Headers printed to console")

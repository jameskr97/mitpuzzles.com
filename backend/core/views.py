from django.db.models.functions import StrIndex, Substr
from django.views.decorators.http import etag
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Value, F
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
        visitor = request.visitor if hasattr(request, "visitor") else None

        queryset = models.Puzzles.objects.all()

        if puzzle_type:
            queryset = queryset.filter(puzzle_type=puzzle_type)
        if variant:
            queryset = queryset.filter(puzzle_class=variant)

        if self.exclude_solved:
            recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(visitor=visitor)).values_list(
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


class PuzzleClassSuffixList(APIView):
    """
    API view that returns distinct suffixes (the part after the dot)
    from all puzzle_class values.
    """
    def get(self, request):
        # get puzzle_type to narrow variant list
        puzzle_type = request.query_params.get('puzzle_type')
        if not puzzle_type:
            return Response(
                {"detail": "puzzle_type query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # annotate each puzzle with the position of the dot and extract the suffix
        qs = (
            models.Puzzles.objects.filter(puzzle_type=puzzle_type)
            .values_list("puzzle_class", flat=True).distinct()
        )
        unique = sorted(set(qs))
        return Response(unique)


class FeedbackAPIView(APIView):
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = serializers.FeedbackSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def submit_game_recording(request):
    serializer = serializers.GameRecordingCreateSerializer(data=request.data, context={"request": request})
    # check if the user already has a recording for this puzzle
    user = request.user if request.user.is_authenticated else None

    existing_recording = models.GameRecording.objects.filter(
        puzzle_id=request.data.get("puzzle"),
        user=user,
        visitor=request.visitor,
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


from .config import generate_settings_etag, get_game_settings
@etag(generate_settings_etag)
@api_view(["GET"])
def game_settings_view(request):
    return Response(get_game_settings())


@api_view(["GET"])
def unsolved_puzzle_count(request):
    user = request.user if request.user.is_authenticated else None

    puzzle_type = request.query_params.get("puzzle_type", None)
    recorded_ids = models.GameRecording.objects.filter(Q(user=user) | Q(visitor=request.visitor)).values_list(
        "puzzle_id", flat=True
    )

    queryset = models.Puzzles.objects.exclude(id__in=recorded_ids)
    if puzzle_type:
        queryset = queryset.filter(puzzle_type=puzzle_type)
    count = queryset.count()

    return Response({"unsolved_count": count})

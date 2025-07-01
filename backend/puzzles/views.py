from django.db.models import Q, Min
from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import  ReadOnlyModelViewSet

from puzzles import models, serializers
from puzzles.models import FreeplayPuzzleAttempt, Puzzle
from puzzles.models.leaderboard import PuzzleAttempt
from puzzles.serializers import LeaderboardEntrySerializer


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

class PuzzleBaseAPIView(APIView):
    exclude_solved = False  # default
    puzzle_type_required = True
    variant_required = True

    def get(self, request):
        #
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

        serializer_class = get_puzzle_serializer(puzzle.puzzle_type)
        return Response(
            {
                "type": "Puzzle",
                "data": {
                    **serializer_class(puzzle).data,
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
            models.Puzzle.objects.filter(puzzle_type=puzzle_type)
            .values_list("puzzle_size", "puzzle_difficulty")
            .distinct()
        )
        unique = sorted(set(qs))
        return Response(unique)


@api_view(["GET"])
def leaderboard_view(request):
    """
    Return a leaderboard of the fastest completion times (in milliseconds) for a
    given puzzle type/size/difficulty, limited to one entry per visitor.

    Query parameters:
        puzzle_type        — required
        puzzle_size        — required
        puzzle_difficulty  — required
        limit              — optional (default 10, max 100)
    """
    puzzle_type = request.GET.get("puzzle_type")
    puzzle_size = request.GET.get("puzzle_size")
    puzzle_difficulty = request.GET.get("puzzle_difficulty")
    limit = min(int(request.GET.get("limit", 10)), 100)

    if not all([puzzle_type, puzzle_size, puzzle_difficulty]):
        return Response({"error": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)

    # Select the best (lowest) completion_time_client_ms per visitor, outputting the visitor's generated_username
    best_times_qs = (
        FreeplayPuzzleAttempt.objects
        .filter(
            puzzle__puzzle_type=puzzle_type,
            puzzle__puzzle_size=puzzle_size,
            puzzle__puzzle_difficulty=puzzle_difficulty,
            completed_at__isnull=False,
            completion_time_client_ms__isnull=False,
        )
        .values("visitor__generated_username")
        .annotate(best_ms=Min("completion_time_client_ms"))
        .filter(best_ms__isnull=False)          # safety
        .order_by("best_ms")[:limit]
    )

    # Build simple leaderboard entries with seconds formatted to two decimals
    leaderboard = []
    for rank, entry in enumerate(best_times_qs, start=1):
        seconds = entry["best_ms"] / 1000.0
        leaderboard.append({
            "rank": rank,
            "username": entry["visitor__generated_username"],
            "duration_display": f"{seconds:.2f} sec",
        })

    return Response({"leaderboard": leaderboard, "count": len(leaderboard)})


class PuzzleDefinitionViewSet(ReadOnlyModelViewSet):
    """
    Read-only viewset for retrieving and formatting existing puzzles.
    Handles:
    - Puzzle retrieval from database
    - Solution hashing for validation
    - Type-specific metadata formatting
    - Frontend-ready puzzle definitions
    """
    queryset = models.Puzzle.objects.filter(puzzle_type__in=['minesweeper', 'sudoku', 'tents', 'kakurasu', 'lightup']).all()

    def get_serializer_class(self):
        return serializers.PuzzleDefinitionSerializer

    @action(detail=False, methods=['get'])
    def random(self, request) -> Response:
        """
        Get a random puzzle of specified type/size/difficulty.

        GET /api/puzzles/random/?puzzle_type=sudoku&size=9x9&difficulty=medium
        """
        puzzle_type = request.query_params.get('puzzle_type')
        size = request.query_params.get('size')
        difficulty = request.query_params.get('difficulty')

        # if no params are given, return completely random puzzle
        if not puzzle_type and not size and not difficulty:
            print("Returning completely random puzzle")
            random_puzzle = self.get_queryset().order_by("?").first()
            serializer = serializers.PuzzleDefinitionSerializer(random_puzzle)
            return Response(serializer.data)

        filter = {}
        if puzzle_type:
            filter['puzzle_type'] = puzzle_type
        if size:
            filter['puzzle_size'] = size
        if difficulty:
            filter['puzzle_difficulty'] = difficulty

        random_puzzle = self.get_queryset().filter(**filter).order_by("?").first()
        serializer = self.get_serializer_class()
        res = serializer(random_puzzle)
        return Response(res.data)

    @action(detail=False, methods=['get'])
    def types(self, request) -> Response:
        """
        Get available puzzle types with their configurations.

        GET /api/puzzles/types/
        """
        puzzle_types = self._get_available_puzzle_types()
        return Response(puzzle_types)

    def _get_available_puzzle_types(self):
        """Get configuration for all available puzzle types."""
        # return "types"
        types_config = {}

        # # Get distinct puzzle types from database
        puzzle_types = list(self.get_queryset().order_by('puzzle_type').distinct('puzzle_type').values_list('puzzle_type', flat=True))

        for puzzle_type in puzzle_types:
            puzzles = Puzzle.objects.filter(puzzle_type=puzzle_type).order_by('puzzle_type')
            difficulty_combinations = list(puzzles.values_list('puzzle_size', 'puzzle_difficulty').distinct())
            types_config[puzzle_type] = {
                'available_difficulties': difficulty_combinations,
                'default_difficulty': difficulty_combinations[0],
                'total_puzzles': puzzles.count()
            }

        return types_config

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from puzzles import models, serializers


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

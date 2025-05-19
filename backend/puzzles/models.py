import uuid

from django.db import models

from accounts.models import User
from core.models import Puzzles, GameRecording
from core.models import make_actor_mixin
from puzzles.engines import get_puzzle_engine
from tracking.models import Visitor


class ActivePuzzleSession(make_actor_mixin("active_puzzles")):
    """
    A live puzzle session.  Maintains the current board state
    and history of moves until the user submits or abandons.
    """

    # metadata
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # puzzle data
    puzzle = models.ForeignKey(Puzzles, on_delete=models.CASCADE, related_name="active_sessions")
    board_state = models.JSONField()
    move_history = models.JSONField(default=list, blank=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        # don't allow multiple sessions for the same puzzle type
        indexes = [models.Index(fields=["updated_at"])]
        ordering = ["-updated_at"]

    @classmethod
    def create_puzzle_session(cls, actor, puzzle_type: str, puzzle_variant: str):
        """Creates a new puzzle session for the given puzzle and user/visitor."""
        # get a random puzzle
        query = dict(puzzle_type=puzzle_type)
        if puzzle_variant:
            query["puzzle_class"] = puzzle_variant
        puzzle = Puzzles.objects.filter(**query).order_by("?").first()

        if not puzzle:
            raise ValueError(f"No puzzle found for type={puzzle_type}, variant={puzzle_variant}")

        # check if a session already exists
        try:
            # if the follow line exists, then the user asked for a new puzzle of an existing puzzle_type
            session = cls.for_actor(actor).get(puzzle__puzzle_type=puzzle_type)
            session.puzzle = puzzle
            session.board_state = []
            session.move_history = []
            session.is_submitted = False
        except cls.DoesNotExist:
            session = cls.objects.create(
                puzzle=puzzle,
                board_state=[],
                move_history=[],
                is_submitted=False,
            )
            session.set_actor(actor)

        puzzle_engine = get_puzzle_engine(session)
        session.board_state = puzzle_engine.create_game_state(puzzle.puzzle_data["board_initial"])
        session.save()
        return session

    @classmethod
    def fetch_for_actor(cls, puzzle_session_id, actor) -> "ActivePuzzleSession | None":
        try:
            session = cls.objects.select_related("puzzle").get(id=puzzle_session_id)
        except cls.DoesNotExist:
            return None

        # ensure that the session belongs to the actor
        owner = session.get_actor()
        if owner is None or owner.id != actor.id:
            return None

        return session

    @classmethod
    def delete_session(cls, session_id, actor):
        """Delete a puzzle session if it belongs to the actor"""
        try:
            session = cls.objects.get(id=session_id, actor=actor)
            session.delete()  # This is the built-in Django delete method
            return True
        except cls.DoesNotExist:
            return False

    def convert_to_game_recording(self):
        """
        Convert the active puzzle session to a game recording.
        This is called when the user submits the correctly solved puzzle.
        """
        """Record a completed puzzle in the GameRecording table"""
        recording_data = {
            "board_state": self.board_state,
            "move_history": self.move_history,
        }

        # Create the game recording
        record = GameRecording.objects.create(puzzle=self.puzzle, data=recording_data)
        record.set_actor(self.get_actor())
        record.save()

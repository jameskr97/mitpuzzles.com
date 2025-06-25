import uuid
from collections import OrderedDict
import asyncio, time
from typing import Dict, Tuple, Callable, Type

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

from protocol.generated.websocket.game_schema import CommandAction, CommandRefresh
from puzzles.abstract import PuzzleDefinition
from puzzles.engine import PUZZLE_TYPE_TO_ENGINE_MAP, PuzzleEngineBase
from puzzles.models import FreeplayPuzzleAttempt, Puzzle
from puzzles.models.puzzle_attempt import AbstractPuzzleAttempt

LRU_LIMIT = 2_000  # or settings.PUZZLES_SESSION_LRU

GAMEMODE_TO_ATTEMPT_TABLE_MAP: Dict[str, Type[AbstractPuzzleAttempt]] = {
    "freeplay": FreeplayPuzzleAttempt,
    # "prolific": ProlificPuzzleAttempt,
}


class EngineWrapper:
    __slots__ = ("engine", "storage", "last_touched")

    def __init__(self, engine, storage):
        self.engine: PuzzleEngineBase = engine
        self.storage: Type[AbstractPuzzleAttempt] = storage
        self.last_touched = time.time()

    def sync_and_flush(self):
        """Sync current board state to the backing DB model."""
        self.storage.board_state = self.engine.board_state
        self.storage.save()
        return self.storage


class SessionManager:
    def __init__(self):
        self._sessions: "OrderedDict[str, EngineWrapper]" = OrderedDict()
        self._by_user_type: Dict[Tuple[str, str], str] = {}
        self._queue = asyncio.Queue()  # flush snapshots to DB

    async def load(self, visitor_id: str, puzzle_type: str, mode: str) -> str:
        """
        Load an existing session or create a new one.
        :param visitor_id: the user identifier (e.g., visitor_id)
        :param puzzle_type: the type of puzzle (e.g., "sudoku", "crossword")
        :param mode: the mode of the session (e.g., "freeplay", "prolific")
        :return: session ID
        """
        # check if we already have this session in memory
        key = (visitor_id, puzzle_type)
        if key in self._by_user_type and self._by_user_type[key] in self._sessions:
            return self._by_user_type[key]

        # get storage_object (where this will be stored while active, but out of memory)
        if mode == "freeplay":
            attempt = await database_sync_to_async(FreeplayPuzzleAttempt.get_or_create_for_actor)(
                visitor_id, puzzle_type=puzzle_type
            )
        elif mode == "prolific":
            raise NotImplementedError("noet yet")
            # session = await database_sync_to_async(ProlificPuzzleSession.get_or_create_for_actor)(visitor_id, puzzle_type=puzzle_type)
        else:
            raise ValueError(f"Unknown session mode: {mode}")

        # create engine
        puzzle_definition = PuzzleDefinition.from_model(attempt.puzzle)
        engine: PuzzleEngineBase = PUZZLE_TYPE_TO_ENGINE_MAP[puzzle_type](puzzle_definition, attempt.board_state)
        wrapper = EngineWrapper(engine, attempt)

        attempt_id = str(attempt.id)
        self._sessions[attempt_id] = wrapper
        self._sessions.move_to_end(attempt_id)
        self._by_user_type[key] = attempt_id
        self._evict_if_needed()
        return attempt_id

    async def get_or_load_wrapper(self, attempt_id: str, mode: str) -> EngineWrapper:
        wrapper = SESSIONS.get_wrapper(attempt_id)
        if wrapper is not None:
            return wrapper

        # If the wrapper isn't loaded (e.g. due to reconnectAion), load from DB
        if mode not in GAMEMODE_TO_ATTEMPT_TABLE_MAP:
            raise ValueError(f"Unknown session mode: {mode}")
        attempt_model = GAMEMODE_TO_ATTEMPT_TABLE_MAP[mode]
        attempt = await database_sync_to_async(attempt_model.objects.select_related("puzzle").get)(id=attempt_id)

        definition = PuzzleDefinition.from_model(attempt.puzzle)
        engine = PUZZLE_TYPE_TO_ENGINE_MAP[attempt.puzzle.puzzle_type](definition, attempt.board_state)
        wrapper = EngineWrapper(engine, attempt)
        self._sessions[attempt_id] = wrapper
        self._sessions.move_to_end(attempt_id)
        return wrapper

    async def refresh(self, cmd: CommandRefresh) -> EngineWrapper:
        """
        Refresh the session by reloading the storage object and engine.
        :param session_id: the ID of the session to refresh
        :return: refreshed EngineWrapper or None if not found
        """
        wrap = self._sessions.get(cmd.session_id)
        if not wrap:
            return None

        new_puzzle = await database_sync_to_async(Puzzle.get_random_puzzle)(
            wrap.storage.puzzle.puzzle_type, cmd.size, cmd.difficulty
        )
        wrap.storage.puzzle = new_puzzle

        definition = PuzzleDefinition.from_model(new_puzzle)
        wrap.engine = PUZZLE_TYPE_TO_ENGINE_MAP[new_puzzle.puzzle_type](definition, [])
        wrap.storage.board_state = wrap.engine.get_initial_board_string()
        wrap.storage.is_solved = False
        wrap.storage.puzzle = new_puzzle
        await database_sync_to_async(wrap.storage.save)()

        return wrap

    def get_wrapper(self, sid: str) -> EngineWrapper | None:
        wrap = self._sessions.get(sid)
        if wrap:
            wrap.last_touched = time.time()
            self._sessions.move_to_end(sid)
        return wrap

    def save(self, session_id, snapshot):
        self._queue.put_nowait(snapshot)  # stub; fleshed later

    # ---------- internals ----------
    def _evict_if_needed(self):
        while len(self._sessions) > LRU_LIMIT:
            sid, wrap = self._sessions.popitem(last=False)  # LRU eviction
            print(f"[TODO] Evicting session {sid} (mode={wrap.mode}, storage={wrap.storage})")

    async def flush_dirty(self):
        """
        Persist every session whose adapter reports itself dirty.
        Call from a background task every N seconds or after each turn.
        """
        for sid, wrap in self._sessions.items():
            adapter = wrap.engine.session
            flush = getattr(adapter, "flush", None)
            if flush:
                flush()  # synchronous DB write


SESSIONS = SessionManager()

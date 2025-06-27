import logging

from puzzles.socket.transport.consumer import logger


class AttemptMissingException(Exception):
    def __init__(self, attempt_id: str, mode: str):
        super().__init__(f"[mode={mode}]: Attempt {attempt_id} not found")
        self.attempt_id = attempt_id


import time
from collections import OrderedDict
from typing import Dict, Tuple, Type

from channels.db import database_sync_to_async

from experiments.models import ExperimentPuzzleAttempt
from protocol.generated.websocket.game_schema import CommandRefresh
from puzzles.abstract import PuzzleDefinition
from puzzles.engine import PUZZLE_TYPE_TO_ENGINE_MAP, PuzzleEngineBase
from puzzles.models import FreeplayPuzzleAttempt, Puzzle
from puzzles.models.puzzle_attempt import AbstractPuzzleAttempt

LRU_LIMIT = 2_000  # or settings.PUZZLES_SESSION_LRU

GAMEMODE_TO_ATTEMPT_TABLE_MAP: Dict[str, Type[AbstractPuzzleAttempt]] = {
    "freeplay": FreeplayPuzzleAttempt,
    "prolific": ExperimentPuzzleAttempt,
}

logger = logging.getLogger(__name__)


class EngineWrapper:
    __slots__ = ("engine", "storage", "last_touched", "mode")

    def __init__(self, engine, storage, mode):
        self.engine: PuzzleEngineBase = engine
        self.storage: Type[AbstractPuzzleAttempt] = storage
        self.last_touched = time.time()
        self.mode = mode

    async def sync_and_flush(self):
        """Sync current board state to the backing DB model."""
        logger.info(f"[SessionManager] Flushing session {self.storage.id}. State: {self.engine.board_state}")
        p = GAMEMODE_TO_ATTEMPT_TABLE_MAP[self.mode].objects.select_related("puzzle")
        # self.storage = await database_sync_to_async(p.get)(id=self.storage.id)

        # self.storage = GAMEMODE_TO_ATTEMPT_TABLE_MAP[self.mode].objects.select_related("puzzle").get(id=self.storage.id)
        self.storage.board_state = self.engine.board_state
        await database_sync_to_async(self.storage.save)()
        return self.storage

    def from_attempt(self, attempt: AbstractPuzzleAttempt):
        self.storage = attempt
        definition = PuzzleDefinition.from_model(attempt.puzzle)
        self.engine = PUZZLE_TYPE_TO_ENGINE_MAP[attempt.puzzle.puzzle_type](definition, attempt.board_state)
        self.last_touched = time.time()
        return self


class SessionManager:
    def __init__(self):
        self._sessions: "OrderedDict[str, EngineWrapper]" = OrderedDict()
        self._by_user_type: Dict[Tuple[str, str], str] = {}

    async def get_or_create_unfinished(
            self, visitor_id: str, puzzle_type: str, mode: str
    ) -> tuple[str, EngineWrapper]:
        """
        Return the active unfinished session for (visitor, type) or create one.
        """
        for sid, wrap in self._sessions.items():
            if (
                    wrap.storage.visitor_id == visitor_id
                    and wrap.storage.puzzle.puzzle_type == puzzle_type
                    and not wrap.storage.is_solved
            ):
                return sid, wrap

        # none found → create first row
        sid = await self.load(visitor_id, puzzle_type, mode="freeplay")
        return sid, self.get_wrapper(sid)

    async def load(self, visitor_id: str, puzzle_type: str, mode: str, forced_id: str | None = None) -> str:
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
        if mode not in GAMEMODE_TO_ATTEMPT_TABLE_MAP:
            raise ValueError(f"Unknown session mode: {mode}")

        attempt_model = GAMEMODE_TO_ATTEMPT_TABLE_MAP[mode]
        attempt: AbstractPuzzleAttempt = await database_sync_to_async(attempt_model.get_or_create_for_actor)(
            visitor_id, puzzle_type=puzzle_type
        )

        # create engine
        puzzle_definition = PuzzleDefinition.from_model(attempt.puzzle)
        engine: PuzzleEngineBase = PUZZLE_TYPE_TO_ENGINE_MAP[puzzle_type](puzzle_definition, attempt.board_state)
        wrapper = EngineWrapper(engine, attempt, mode)
        await wrapper.sync_and_flush()

        attempt_id = forced_id or str(attempt.id)
        if forced_id:
            attempt.id = forced_id

        self._sessions[attempt_id] = wrapper
        self._sessions.move_to_end(attempt_id)
        self._by_user_type[key] = attempt_id
        self._evict_if_needed()
        return attempt_id

    async def get_or_load_wrapper(self, attempt_id: str, mode: str) -> EngineWrapper:
        wrapper = SESSIONS.get_wrapper(attempt_id)
        if wrapper is not None:
            return wrapper

        attempt_model = GAMEMODE_TO_ATTEMPT_TABLE_MAP[mode]
        try:
            attempt = await database_sync_to_async(attempt_model.objects.select_related("puzzle").get)(id=attempt_id)
        except attempt_model.DoesNotExist:
            # Row vanished (deleted/pruned) → let caller decide how to proceed.
            raise AttemptMissingException(attempt_id, mode)

        definition = PuzzleDefinition.from_model(attempt.puzzle)
        engine = PUZZLE_TYPE_TO_ENGINE_MAP[attempt.puzzle.puzzle_type](definition, attempt.board_state)
        wrapper = EngineWrapper(engine, attempt, mode)
        self._sessions[attempt_id] = wrapper
        self._sessions.move_to_end(attempt_id)
        return wrapper

    async def refresh(self, cmd: CommandRefresh, visitor_id: str, mode: str) -> EngineWrapper:
        """
        Refresh the session by reloading the storage object and engine.
        :param attempt_id: the ID of the session to refresh
        :return: refreshed EngineWrapper or None if not found
        """
        wrap = self._sessions.get(cmd.attempt_id)
        if not wrap:
            return None

        if mode != "freeplay":
            raise ValueError("Refresh is only supported in freeplay mode")

        # this puzzle is now solved. we need a new row for this user.
        # delete the old one from memory, and create a new one.
        if wrap.storage.is_solved:
            del self._sessions[cmd.attempt_id]
            sid = await self.load(visitor_id, wrap.storage.puzzle.puzzle_type, mode="freeplay")
            wrap = self._sessions.get(sid)
            wrap.engine.board_state = wrap.engine.get_initial_board_string()
            return self._sessions.get(sid)

        new_puzzle = await database_sync_to_async(Puzzle.get_random_puzzle)(
            wrap.storage.puzzle.puzzle_type, cmd.size, cmd.difficulty
        )
        wrap.storage.puzzle = new_puzzle

        definition = PuzzleDefinition.from_model(new_puzzle)
        wrap.engine = PUZZLE_TYPE_TO_ENGINE_MAP[new_puzzle.puzzle_type](definition, [])
        wrap.storage.board_state = wrap.engine.get_initial_board_string()
        wrap.storage.is_solved = False
        wrap.storage.puzzle = new_puzzle
        wrap.storage.action_history = []
        if hasattr(wrap.storage, "used_tutorial"):
            wrap.storage.used_tutorial = False
        await wrap.sync_and_flush()
        return wrap

    def get_wrapper(self, sid: str) -> EngineWrapper | None:
        wrap = self._sessions.get(sid)
        if wrap:
            wrap.last_touched = time.time()
            self._sessions.move_to_end(sid)
        return wrap

    def save(self, attempt_id, snapshot):
        self._queue.put_nowait(snapshot)  # stub; fleshed later

    # ---------- internals ----------
    def _evict_if_needed(self):
        while len(self._sessions) > LRU_LIMIT:
            sid, wrap = self._sessions.popitem(last=False)  # LRU eviction
            print(f"[TODO] Evicting session {sid} (mode={wrap.mode}, storage={wrap.storage})")

    def flush_dirty(self):
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

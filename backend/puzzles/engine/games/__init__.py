from __future__ import annotations

from typing import TYPE_CHECKING

from puzzles.engine.games.base import PuzzleEngineBase
from .kakurasu import KakurasuEngine
from .lightup import LightupEngine
from .minesweeper import MinesweeperEngine
from .sudoku import SudokuEngine
from .tents import TentsEngine

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

_REGISTRY = {
    "minesweeper": MinesweeperEngine,
    "sudoku": SudokuEngine,
    "tents": TentsEngine,
    "kakurasu": KakurasuEngine,
    "lightup": LightupEngine,
}


def get_puzzle_engine(puzzle_session: ActivePuzzleSession) -> PuzzleEngineBase:
    try:
        engine_class = _REGISTRY[puzzle_session.puzzle.puzzle_type]
        engine_instance = engine_class(puzzle_session)
        return engine_instance
    except KeyError:
        raise ValueError(f"No engine registered for puzzle_type={puzzle_session.puzzle.puzzle_type}")

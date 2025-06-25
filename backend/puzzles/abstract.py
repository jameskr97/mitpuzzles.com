import copy
from dataclasses import dataclass, field
from typing import Any

from puzzles.models import Puzzle


@dataclass(frozen=True, slots=True)
class PuzzleDefinition:
    """Immutable description of one pre-generated puzzle."""
    id: str
    type: str
    rows: int
    cols: int
    initial_state: list[int]
    solution_state: list[int]
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_model(cls, puzzle: Puzzle) -> "PuzzleDefinition":
        puzzle_meta = copy.deepcopy(puzzle.puzzle_data)
        puzzle_meta.pop("difficulty", None)
        puzzle_meta.pop("idx", None)

        rows = puzzle_meta.pop("rows", puzzle_meta.pop("n_rows", 0))
        cols = puzzle_meta.pop("cols", puzzle_meta.pop("n_cols", 0))
        initial_state = puzzle_meta.pop("game_state")
        solution_state = puzzle_meta.pop("game_board", [])

        return cls(
            id=str(puzzle.id),
            type=puzzle.puzzle_type,
            rows=rows,
            cols=cols,
            initial_state=initial_state,
            solution_state=solution_state,
            meta=puzzle_meta,
        )

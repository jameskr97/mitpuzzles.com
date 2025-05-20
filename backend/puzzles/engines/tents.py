from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engines.base import PuzzleEngineBase, State

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class TentCellStates(IntEnum):
    Empty = 0
    Tree = 1
    Tent = 2
    Green = 3


class TentsEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(puzzle_session, allowed_states=[
            TentCellStates.Empty,
            TentCellStates.Tent,
            TentCellStates.Green
        ])

    def can_modify_cell(self, state: State, row: int, col: int) -> bool:
        cell = self.get_initial_board_string()
        return int(cell) != TentCellStates.Tree

    def serialize_gamedata(self) -> dict:
        """
        Serialize the game data to a dictionary.
        This is used for saving the game state to the database.
        """
        return {
            "rows": self.rows,
            "cols": self.cols,
            "board": self.puzzle_session.board_state,
            "col_counts": self.puzzle_data["col_tent_counts"],
            "row_counts": self.puzzle_data["row_tent_counts"],
        }

from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engines.base import PuzzleEngineBase, State

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class LightupCellStates(IntEnum):
    Wall0 = 0
    Wall1 = 1
    Wall2 = 2
    Wall3 = 3
    Wall4 = 4
    WallBlack = 5
    Empty = 6
    Bulb = 7
    Cross = 8

# 1.111...11.111..111...1.2.2.1..53.....1.....151.5
class LightupEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(puzzle_session, allowed_states=[
            LightupCellStates.Empty,
            LightupCellStates.Bulb,
            LightupCellStates.Cross
        ])

    def is_solved(self, strict=False) -> bool:
        """
        Lightup ignores strict mode.
        """
        s = "".join(str(cell) for cell in self.get_board_state())
        s = s.replace("6", "0")
        return s == self.get_solution_board_string()

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        # you can only modify empty cells
        board = self.get_initial_board_string()
        cell = int(board[row * self.cols + col])
        return cell == LightupCellStates.Empty

    def serialize_gamedata(self) -> dict:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "board": self.get_board_state()
        }

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

    def create_game_state(self, initial_state: str) -> list:
        """Create a new game state based on the puzzle data."""
        res = []
        for c in initial_state:
            match c:
                case "0" | "1" | "2" | "3" | "4" | "5" : res.append(int(c))
                case ".": res.append(LightupCellStates.Empty)
                case _: raise ValueError(f"Invalid initial_board: {c}")
        return res

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        # you can only modify empty cells
        if self.puzzle_data["board_initial"][row * self.cols + col] != ".":
            return False
        return True

    def serialize_gamedata(self) -> dict:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "board": self.puzzle_session.board_state,
        }

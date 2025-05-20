from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engines.base import PuzzleEngineBase, State

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class CellStatesMinesweeper(IntEnum):
    UNMARKED = 10
    FLAG = 11
    SAFE = 12


class MinesweeperEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(
            puzzle_session,
            allowed_states=CellStatesMinesweeper,
        )

    def create_game_state(self) -> list:
        """Create a new game state based on the puzzle data."""
        initial_state = self.get_initial_board_string()
        as_list = list(initial_state)
        res = []
        for cell in as_list:
            match cell:
                case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8": res.append(int(cell))
                case "F": res.append(CellStatesMinesweeper.FLAG)
                case "S": res.append(CellStatesMinesweeper.SAFE)
                case "_": res.append(CellStatesMinesweeper.UNMARKED)
                case _: raise ValueError(f"Invalid initial_board: {initial_state}")
        return res

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        mask = self.get_initial_board_string()
        if mask is None:
            return True
        idx = row * self.cols + col
        return mask[idx] in ("_", 0, "")

    def serialize_gamedata(self) -> dict:
        """
        Serialize the game data to a dictionary.
        This is used to send the game data to the client.
        """
        return {
            "rows": self.rows,
            "cols": self.cols,
            "board": self.puzzle_session.board_state,
        }

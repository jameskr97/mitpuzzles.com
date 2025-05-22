from enum import IntEnum
from collections import Counter
from typing import TYPE_CHECKING
import string

from puzzles.converters import TR_MINESWEEPER
from puzzles.engines.base import PuzzleEngineBase, State
# sequential monte carlo algorithm
# differential rendering
#
if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class CellStatesMinesweeper(IntEnum):
    UNMARKED = 9
    FLAG = 10
    SAFE = 11


class MinesweeperEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(
            puzzle_session,
            allowed_states=CellStatesMinesweeper,
        )

    def is_solved(self, strict=False) -> bool:
        board = [string.ascii_lowercase[i] for i in  self.get_board_state()]
        if strict:
            solution = self.get_solution_board_string()
            res = "".join([string.ascii_lowercase[i] for i in board])
            return res == solution

        # invariant - non-strict mode. ensure that only flags are in correct positions ignoring if other cells are correct
        solution = self.get_solution_board_string()
        flag_repr = string.ascii_lowercase[CellStatesMinesweeper.FLAG]
        # get a list of indexes of the flags in the solution and the board
        # make sure these lists match
        solution_flag_indexes = [i for i, cell in enumerate(solution) if cell == flag_repr]
        board_flag_indexes = [i for i, cell in enumerate(board) if cell == flag_repr]
        return Counter(solution_flag_indexes) == Counter(board_flag_indexes)


    def create_game_state(self) -> list:
        """Create a new game state based on the puzzle data."""
        initial_state = self.get_initial_board_string()
        as_list = list(initial_state)
        res = [string.ascii_lowercase.find(i) for i in initial_state]
        # res = []
        # for cell in as_list:
        #     i = string.ascii_lowercase.find(cell)
        #
        #     match cell:
        #         case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8": res.append(int(cell))
        #         case "F": res.append(CellStatesMinesweeper.FLAG)
        #         case "S": res.append(CellStatesMinesweeper.SAFE)
        #         case "U": res.append(CellStatesMinesweeper.UNMARKED)
        #         case _: raise ValueError(f"Invalid initial_board: {initial_state}")
        return res

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        board = self.get_initial_board_string()
        index = row * self.cols + col
        cell = board[index]
        value = string.ascii_lowercase.find(cell)
        return value == CellStatesMinesweeper.UNMARKED

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

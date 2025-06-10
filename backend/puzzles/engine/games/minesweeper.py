import string
from collections import Counter
from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engine.games.base import PuzzleEngineBase, State
from puzzles.engine.handlers.generic.state_cycling import StateCyclingInputHandler
from puzzles.engine.rules.minesweeper import numbered_cell_flag_validator

# sequential monte carlo algorithm
# differential rendering
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
            input_handler=StateCyclingInputHandler([CellStatesMinesweeper.UNMARKED, CellStatesMinesweeper.FLAG, CellStatesMinesweeper.SAFE]),
            validation_constraints=[numbered_cell_flag_validator()]
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

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        board = self.get_initial_board_string()
        raw_cell_value = board[row * self.cols + col]
        return int(raw_cell_value) == CellStatesMinesweeper.UNMARKED

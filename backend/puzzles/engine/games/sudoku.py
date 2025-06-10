from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engine.games.base import PuzzleEngineBase, State
from puzzles.engine.handlers.sudoku_input import SudokuInputHandler
from puzzles.engine.rules.sudoku import no_duplicate_numbers_in_rows, no_duplicate_numbers_in_cols, \
    no_duplicate_numbers_in_boxes

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class SudokuCellStates(IntEnum):
    Empty = 0
    Filled = 1
    Crossed = 2


class SudokuEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(puzzle_session, input_handler=SudokuInputHandler(), validation_constraints=[
            no_duplicate_numbers_in_rows(),
            no_duplicate_numbers_in_cols(),
            no_duplicate_numbers_in_boxes(),
        ])

    def is_solved(self, strict=False) -> bool:
        """
        Check if the Sudoku puzzle is solved.
        :param strict: Ignored. Sudoku is inherently strict.
        :return:
        """
        board = "".join([str(c) for c in self.get_board_state()])
        solution = "".join([str(c) for c in self.get_solution_board_string()])
        return board == solution

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        initial_board = self.get_initial_board_string()

        return initial_board[row * self.cols + col] == 0

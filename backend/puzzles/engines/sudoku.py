from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engines.base import PuzzleEngineBase, State

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class SudokuCellStates(IntEnum):
    Empty = 0
    Filled = 1
    Crossed = 2


class SudokuEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(puzzle_session)

    def is_solved(self, strict=False) -> bool:
        """
        Check if the Sudoku puzzle is solved.
        :param strict: Ignored. Sudoku is inherently strict.
        :return:
        """
        board = "".join([str(c) for c in self.get_board_state()])
        solution = self.get_solution_board_string()
        return board == solution

    def on_cell_click(self, row: int, col: int, button: int = 0, state_override=None) -> bool:
        if isinstance(state_override, str):
            state_override = int(state_override)

        # sudoku needs a state to be set
        if state_override is None:
            return False

        # don't allow a cell to be set to a number greater than the width.height
        if state_override > self.cols:
            return False

        # modify the cell state
        self.puzzle_session.board_state[row * self.cols + col] = state_override
        return True


    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        return self.puzzle_data["board_initial"][row * self.cols + col] == "0"

    def serialize_gamedata(self) -> dict:
        """
        Serialize the game data to a dictionary.
        This is used for saving the game state to the database.
        """
        return {
            "rows": self.rows,
            "cols": self.cols,
            "board": self.get_board_state(),
            "board_initial": self.get_initial_board_string()
        }

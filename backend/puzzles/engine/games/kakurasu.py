from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.abstract import PuzzleDefinition
from puzzles.engine.games.base import PuzzleEngineBase, State
from puzzles.engine.handlers.generic.state_cycling import StateCyclingInputHandler
from puzzles.engine.handlers.generic.line_state_toggler import LineStateToggler
from puzzles.engine.rules.generic.line_sum import validate_line_sums, validate_line_sums_exceeded, \
    validate_line_all_negative

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession


class KakurasuCellStates(IntEnum):
    Empty = 0
    Filled = 1
    Crossed = 2


class KakurasuEngine(PuzzleEngineBase):
    def __init__(self, definition: PuzzleDefinition, board_state: State) -> None:
        super().__init__(
            definition,
            board_state,
            input_handler=[
                StateCyclingInputHandler(KakurasuCellStates),
                LineStateToggler(KakurasuCellStates.Empty, KakurasuCellStates.Crossed),
            ],
            validation_constraints=[
                validate_line_sums("row", KakurasuCellStates.Filled, "row_sums", True),
                validate_line_sums("col", KakurasuCellStates.Filled, "col_sums", True),
                validate_line_all_negative("row", KakurasuCellStates.Crossed, "row_sums"),
                validate_line_all_negative("col", KakurasuCellStates.Crossed, "col_sums"),
            ],
            extra_gamedata_fields={
                "row_sums": "row_sums",
                "col_sums": "col_sums",
            }
        )

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        return True

    def is_solved(self, strict=False):
        """
        Checks if user input is valid against a solution.

        non-strict mode: all 1 in solution must match all 1 in input. no extra 1
            strict mode: non-strict + all 0 in solution must be marked as 2
        Args:
            strict (bool): Whether to use strict mode validation (default: False)
        Returns:
            bool: True if the input is valid, False otherwise
        """
        board = "".join(str(cell) for cell in self.board_state)
        solution = "".join(str(cell) for cell in self.get_solution_board_string())

        if strict:
            strict_solution = "".join("2" if cell == "0" else cell for cell in solution)
            return board == strict_solution

        # If strict mode is not enabled, ignore the cross in the user board
        black_only_board = "".join("1" if cell == "1" else "0" for cell in board)
        return black_only_board == solution

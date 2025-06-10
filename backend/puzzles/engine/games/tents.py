from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engine.games.base import PuzzleEngineBase, State
from puzzles.engine.handlers.generic.line_state_toggler import LineStateToggler
from puzzles.engine.handlers.generic.state_cycling import StateCyclingInputHandler
from puzzles.engine.rules.generic.line_sum import validate_line_sums_exceeded, validate_line_all_negative
from puzzles.engine.rules.tents import no_adjacent_tents, validate_trees_have_tent_access

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

class TentCellStates(IntEnum):
    Empty = 0
    Tree = 1
    Tent = 2
    Green = 3


class TentsEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(
            puzzle_session,
            input_handler=[
                StateCyclingInputHandler([TentCellStates.Empty, TentCellStates.Tent, TentCellStates.Green]),
                LineStateToggler(TentCellStates.Empty, TentCellStates.Green),
            ],
            validation_constraints=[
                no_adjacent_tents(),
                validate_trees_have_tent_access(),
                validate_line_sums_exceeded("row", TentCellStates.Tent, "row_tent_counts"),
                validate_line_sums_exceeded("col", TentCellStates.Tent, "col_tent_counts"),
                validate_line_all_negative("row", TentCellStates.Green, "row_tent_counts", ignored_values=[TentCellStates.Tree]),
                validate_line_all_negative("col", TentCellStates.Green, "col_tent_counts", ignored_values=[TentCellStates.Tree]),
            ],
            extra_gamedata_fields={
                "row_tent_counts": "row_counts",
                "col_tent_counts": "col_counts",
            },
        )

    def is_solved(self, strict=False) -> bool:
        if not strict:
            # In non-strict mode, we only check if the number of tents matches the solution
            board_tents = "".join([str(c) if c == TentCellStates.Tent else "0" for c in self.get_board_state()])
            solution_tents = "".join([str(c) if int(c) == TentCellStates.Tent else "0" for c in self.get_solution_board_string()])
            return board_tents == solution_tents

        # In strict mode, we check if the board matches the solution exactly
        board = "".join([str(c) for c in self.get_board_state()])
        solution = self.get_solution_board_string()
        return board == solution

    def can_modify_cell(self, state: State, row: int, col: int) -> bool:
        board = self.get_initial_board_string()
        index = row * self.cols + col
        return int(board[index]) != TentCellStates.Tree

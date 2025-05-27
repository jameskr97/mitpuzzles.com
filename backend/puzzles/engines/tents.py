from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engines.base import PuzzleEngineBase, State
from puzzles.engines.ops import PuzzleOps

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

    def on_row_click(self, row: int) -> bool:
        PuzzleOps.change_line_state(
            is_row=True,
            index=row,
            board=self.puzzle_session.board_state,
            rows=self.rows,
            cols=self.cols,
            from_state=TentCellStates.Empty,
            to_state=TentCellStates.Green,
        )
        self.save_active_puzzle()
        return True

    def on_col_click(self, col: int) -> bool:
        PuzzleOps.change_line_state(
            is_row=False,
            index=col,
            board=self.puzzle_session.board_state,
            rows=self.rows,
            cols=self.cols,
            from_state=TentCellStates.Empty,
            to_state=TentCellStates.Green,
        )
        self.save_active_puzzle()
        return True

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

from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.abstract import PuzzleDefinition
from puzzles.engine.games.base import PuzzleEngineBase, State
from puzzles.engine.handlers.generic.state_cycling import StateCyclingInputHandler
from puzzles.engine.rules.lightup import validate_numbered_wall_constraints

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

class LightupEngine(PuzzleEngineBase):
    def __init__(self, definition: PuzzleDefinition, board_state: State) -> None:
        from puzzles.engine.rules.lightup import no_bulbs_lighting_each_other
        super().__init__(
            definition,
            board_state,
            input_handler=StateCyclingInputHandler([
                LightupCellStates.Empty,
                LightupCellStates.Bulb,
                LightupCellStates.Cross
            ]),
            validation_constraints=[no_bulbs_lighting_each_other(), validate_numbered_wall_constraints()],
        )

    def is_solved(self, strict=False) -> bool:
        """
        Lightup ignores strict mode.
        Only check if the light bulbs are placed correctly.
        """
        def get_bulb_only_string(board_state: State) -> str:
            return "".join(["1" if int(cell) == LightupCellStates.Bulb else "0" for cell in board_state])
        user_bulbs = get_bulb_only_string(self.board_state)
        solution_bulbs = get_bulb_only_string(self.get_solution_board_string())
        return user_bulbs == solution_bulbs

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        # you can only modify empty cells
        board = self.get_initial_board_string()
        cell = int(board[row * self.cols + col])
        return cell == LightupCellStates.Empty

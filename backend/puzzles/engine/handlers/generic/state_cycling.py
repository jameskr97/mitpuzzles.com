from typing import Union, Type, List
from enum import Enum

from puzzles.engine.games.base import InputHandler, PuzzleEngineBase
from puzzles.engine.games.ops import PuzzleOps


class StateCyclingInputHandler(InputHandler):
    class CycleDirection:
        FORWARD = 0
        BACKWARD = 1

    def __init__(self, allowed_states: Union[Type[Enum], List[int]] = None):
        """
        :param allowed_states: A list of numerical values to pass through (typically a list of specific enums value)
                               or an enum itself, when all possible values are allowed.
        """
        if isinstance(allowed_states, type) and issubclass(allowed_states, Enum):
            self.allowed_states: List[int] = [e.value for e in allowed_states]
        else:
            self.allowed_states: List[int] = allowed_states or []

    def on_cell_click(self, engine: PuzzleEngineBase, row: int, col: int, button: str = "left", desired_state=None) -> bool:
        board = engine.puzzle_session.board_state

        # If a specific state is requested, don't cycle
        if desired_state is not None:
            PuzzleOps.set_cell_state(board, row, col, engine.cols, desired_state)
            return True

        cycle = StateCyclingInputHandler.CycleDirection.FORWARD
        if button == "right":
            cycle = StateCyclingInputHandler.CycleDirection.BACKWARD
        PuzzleOps.cycle_cell(board, row, col, engine.cols, self.allowed_states, cycle)
        return True

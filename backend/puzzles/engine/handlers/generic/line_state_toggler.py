from puzzles.engine.games.ops import PuzzleOps
from puzzles.engine.handlers.interface import InputHandler


class LineStateToggler(InputHandler):
    def __init__(self, from_state, to_state):
        self.from_state = from_state
        self.to_state = to_state

    def on_row_click(self, engine, row: int, button: int = 0) -> bool:
        PuzzleOps.change_line_state(
            is_row=True,
            index=row,
            board=engine.get_board_state(),
            rows=engine.rows,
            cols=engine.cols,
            from_state=self.from_state,
            to_state=self.to_state,
        )
        return True

    def on_col_click(self, engine, col: int, button: int = 0) -> bool:
        PuzzleOps.change_line_state(
            is_row=False,
            index=col,
            board=engine.get_board_state(),
            rows=engine.rows,
            cols=engine.cols,
            from_state=self.from_state,
            to_state=self.to_state,
        )
        return True

from puzzles.engine.handlers.interface import InputHandler


class SudokuInputHandler(InputHandler):
    def on_cell_click(self, engine, row: int, col: int, button: int = 0, state_override=None) -> bool:
        if isinstance(state_override, str):
            try:
                state_override = int(state_override)
            except ValueError:
                return False

        if state_override is None:
            return False
        if state_override > engine.cols:
            return False

        engine.board_state[row * engine.cols + col] = state_override
        return True

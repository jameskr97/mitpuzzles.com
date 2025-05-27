from typing import List


class PuzzleOps:
    @staticmethod
    def cell_index(row: int, col: int, cols: int) -> int:
        return row * cols + col

    @staticmethod
    def set_cell_state(board: List[int], row: int, col: int, cols: int, state: int) -> None:
        index = PuzzleOps.cell_index(row, col, cols)
        board[index] = state

    @staticmethod
    def cycle_cell(
        board: List[int], row: int, col: int, cols: int, allowed_states: List[int], direction: int = 0
    ) -> None:
        index = row * cols + col
        current = board[index]
        try:
            i = allowed_states.index(current)
        except ValueError:
            board[index] = allowed_states[0]
            return

        step = 1 if direction == 0 else -1
        board[index] = allowed_states[(i + step) % len(allowed_states)]

    @staticmethod
    def change_line_state(
        is_row: bool,
        index: int,
        board: List[int],
        rows: int,
        cols: int,
        from_state: int,
        to_state: int,
    ) -> None:
        relevant = []

        for i in range(cols if is_row else rows):
            row = index if is_row else i
            col = i if is_row else index
            idx = row * cols + col
            relevant.append(idx)

        # Check if any cell is empty
        if any(board[i] == 0 for i in relevant):
            for i in relevant:
                if board[i] == 0:
                    board[i] = to_state
        else:
            # Toggle between from_state and to_state
            for i in relevant:
                if board[i] == from_state:
                    board[i] = to_state
                elif board[i] == to_state:
                    board[i] = from_state

export class PuzzleOps {
  static cell_index(row: number, col: number, cols: number): number {
    return row * cols + col;
  }

  static set_cell_state(board: number[][], row: number, col: number, state: number): void {
    board[row][col] = state;
  }

  static cycle_cell(
    board: number[][],
    row: number,
    col: number,
    allowed_states: number[],
    direction: number = 0,
  ): void {
    const current = board[row][col];
    let index: number;

    try {
      index = allowed_states.indexOf(current);
      if (index === -1) {
        board[row][col] = allowed_states[0];
        return;
      }
    } catch {
      board[row][col] = allowed_states[0];
      return;
    }

    const step = direction === 0 ? 1 : -1;
    board[row][col] = allowed_states[(index + step + allowed_states.length) % allowed_states.length];
  }

  static change_line_state(
    is_row: boolean,
    index: number,
    board: number[][],
    rows: number,
    cols: number,
    from_state: number,
    to_state: number,
  ): void {
    const relevant: Array<{ row: number; col: number }> = [];

    // Collect relevant cell coordinates
    for (let i = 0; i < (is_row ? cols : rows); i++) {
      const row = is_row ? index : i;
      const col = is_row ? i : index;
      relevant.push({ row, col });
    }

    // Check if any cell is empty (state 0)
    const hasEmpty = relevant.some(({ row, col }) => board[row][col] === 0);
    if (hasEmpty) {
      // Set all empty cells to to_state
      for (const { row, col } of relevant) {
        if (board[row][col] === 0) {
          board[row][col] = to_state;
        }
      }
    } else {
      // Toggle between from_state and to_state
      for (const { row, col } of relevant) {
        if (board[row][col] === from_state) {
          board[row][col] = to_state;
        } else if (board[row][col] === to_state) {
          board[row][col] = from_state;
        }
      }
    }
  }
}

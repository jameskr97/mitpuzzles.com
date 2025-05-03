type EmitCallback = (event: string, payload?: any) => void;

export enum TentCellStates {
  Empty = 0,
  Tent = 1,
  Green = 2,
  NUM_STATES,
}

export interface TentsState {
  rows: number;
  cols: number;
  trees: number[];
  cell_states: number[];
  row_counts: number[];
  col_counts: number[];
  board_solution_hash: string;
}

export class ModelTentsPuzzle {
  readonly ROWS: number;
  readonly COLS: number;

  // Event Tracking
  private HOVER_TIME_MINIMUM: number = 2000; // ms
  private hover_enter_time?: number;

  constructor(
    private puzzle: TentsState,
    private emit: EmitCallback,
  ) {
    this.ROWS = puzzle.rows;
    this.COLS = puzzle.cols;
  }

  ////////////////////////////////////////////////////////////
  //// Game Creation + Model Request
  isCellTree(row: number, col: number) {
    return this.puzzle.trees[row * this.COLS + col] === 1;
  }

  isCellTent(row: number, col: number) {
    return this.puzzle.cell_states[row * this.COLS + col] === TentCellStates.Tent;
  }

  isCellGreen(row: number, col: number) {
    return this.puzzle.cell_states[row * this.COLS + col] === TentCellStates.Green;
  }

  getTopNumber(col: number) {
    return this.puzzle.col_counts[col];
  }

  getLeftNumber(row: number) {
    return this.puzzle.row_counts[row];
  }

  // return true if the cell is next to a tree horizontally, vertically, or diagonally
  isCellAdjacentToTent(row: number, col: number) {
    const neighbors = this.getNeighboringCells(row, col);
    neighbors.push([row, col]); // include the current cell
    for (const [r, c] of neighbors) {
      if (this.puzzle.cell_states[r * this.COLS + c] === TentCellStates.Tent) {
        return true;
      }
    }
  }

  getNeighboringCells(row: number, col: number): [number, number][] {
    const neighbors: [number, number][] = [];

    // -1 to 1 inclusive so we can just add the offset to the current row/col
    for (let i = -1; i <= 1; i++) {
      for (let j = -1; j <= 1; j++) {
        // Skip the current cell
        if (i === 0 && j === 0) continue;

        // Calculate the new row and column
        const newRow = row + i;
        const newCol = col + j;

        // Skip if out of bounds
        if (newRow < 0 || newRow >= this.ROWS) continue;
        if (newCol < 0 || newCol >= this.COLS) continue;

        // Add the neighbor
        neighbors.push([newRow, newCol]);
      }
    }
    return neighbors;
  }

  ////////////////////////////////////////////////////////////
  //// Event Handlers
  onCellMouseEnter(row: number, col: number): void {
    if (this.isCellTree(row, col)) return;
    this.hover_enter_time = Date.now();
  }

  onCellMouseLeave(row: number, col: number): void {
    const time_leave = Date.now();
    if (this.hover_enter_time === undefined) return;
    const time_diff = time_leave - this.hover_enter_time;
    if (time_diff < this.HOVER_TIME_MINIMUM) return;

    const index = row * this.COLS + col;
    this.emit("cell-hovered", { index: index, hover_time: time_diff });
  }

  onCellClick(row: number, col: number, event: MouseEvent) {
    const index = row * this.COLS + col;
    if (this.puzzle.trees[index] === 1) return;
    const state = this.puzzle.cell_states[index];

    // go backwards if right click
    if (event.button === 2) {
      this.puzzle.cell_states[index] = (state + TentCellStates.NUM_STATES - 1) % TentCellStates.NUM_STATES;
    } else {
      this.puzzle.cell_states[index] = (state + 1) % TentCellStates.NUM_STATES;
    }
    this.emit("cell-changed", { index, has_tent: true });
  }

  onRowNumberClick(row: number) {
    const modifiedIndexes: number[] = [];
    for (let col = 0; col < this.COLS; col++) {
      const index = row * this.COLS + col;
      if (this.puzzle.trees[index] === 1) continue;
      if (this.puzzle.cell_states[index] !== TentCellStates.Empty) continue;
      this.puzzle.cell_states[index] = TentCellStates.Green;
      modifiedIndexes.push(index);
    }
    if (modifiedIndexes.length > 0) {
      this.emit("cells-changed", { indexes: modifiedIndexes, has_green: true });
    }
  }

  onColNumberClick(col: number) {
    const modifiedIndexes: number[] = [];
    for (let row = 0; row < this.ROWS; row++) {
      const index = row * this.COLS + col;
      if (this.puzzle.trees[index] === 1) continue;
      if (this.puzzle.cell_states[index] !== TentCellStates.Empty) continue;
      this.puzzle.cell_states[index] = TentCellStates.Green;
      modifiedIndexes.push(index);
    }
    if (modifiedIndexes.length > 0) {
      this.emit("cells-changed", { indexes: modifiedIndexes, has_green: true });
    }
  }
}

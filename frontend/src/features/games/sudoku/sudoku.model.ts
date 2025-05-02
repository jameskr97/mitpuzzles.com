/**
 * Sudoku Puzzle Model
 *
 * The following diagram is a representation of what will be
 * returned by the getRow, getCol, and getSquare methods.
 * All numbers apart of that row will be returned in an array.
 *
    |1 2 3|4 5 6|7 8 9|
  --|- - -|- - -|- - -|
  1 |     |     |     |
  2 |  1  |  2  |  3  |
  3 |     |     |     |
  --|- - -|- - -|- - -|
  4 |     |     |     |
  5 |  4  |  5  |  6  |
  6 |     |     |     |
  --|- - -|- - -|- - -|
  7 |     |     |     |
  8 |  7  |  8  |  9  |
  9 |     |     |     |
  --|- - -|- - -|- - -|
 *
 */
import { ref, type Ref } from "vue";

type EmitCallback = (event: string, payload?: any) => void;
export interface SudokuState {
  rows: number;
  cols: number;
  /** The base grid of the sudoku board that will remain unmodified */
  base_grid: number[];
  /** The grid of the sudoku board which the user entered */
  user_grid: number[];
}

export class ModelSudokuPuzzle {
  readonly ROWS: number;
  readonly COLS: number;

  active_cell: Ref<[number, number] | null>;

  constructor(
    private puzzle: SudokuState,
    private emit: EmitCallback,
  ) {
    this.ROWS = puzzle.rows;
    this.COLS = puzzle.cols;
    this.active_cell = ref(null);
  }

  ////////////////////////////////////////////////////////////
  //// Game Creation + Model Request
  canModifyCell(row: number, col: number) {
    return this.puzzle.base_grid[row * this.COLS + col] === 0;
  }

  isSquareSelected(row: number, col: number) {
    if (this.active_cell.value === null) return false;
    const [active_row, active_col] = this.active_cell.value;
    return Math.floor(active_row / 2) === Math.floor(row / 2) && Math.floor(active_col / 2) === Math.floor(col / 2);
  }

  isRowSelected(row: number) {
    return this.active_cell.value && this.active_cell.value[0] === row;
  }
  isColSelected(col: number) {
    return this.active_cell.value && this.active_cell.value[1] === col;
  }
  isCellActive(row: number, col: number) {
    return this.active_cell.value && this.active_cell.value[0] === row && this.active_cell.value[1] === col;
  }

  getCellDisplay(row: number, col: number) {
    const index = row * this.COLS + col;
    if (this.puzzle.base_grid[index] !== 0) return this.puzzle.base_grid[index];

    const user_value = this.puzzle.user_grid[index];
    return user_value === 0 ? " " : user_value;
  }

  ////////////////////////////////////////////////////////////
  //// Grid Subdivision
  getRow(row: number) {
    return this.puzzle.base_grid.slice(row * this.COLS, row * this.COLS + this.COLS);
  }
  getCol(col: number) {
    return this.puzzle.base_grid.filter((_, i) => i % this.COLS === col);
  }
  getSquare(row: number, col: number) {
    const startRow = Math.floor(row / 3) * 3;
    const startCol = Math.floor(col / 3) * 3;
    const square = [];
    for (let i = startRow; i < startRow + 3; i++) {
      for (let j = startCol; j < startCol + 3; j++) {
        square.push(this.puzzle.base_grid[i * this.COLS + j]);
      }
    }
    return square;
  }

  ////////////////////////////////////////////////////////////
  //// Game Logic
  isSubdivisionUnique(subdivision: number[]): boolean {
    return new Set(subdivision).size === subdivision.length;
  }
  isGridValid(): boolean {
    for (let i = 0; i < this.ROWS; i++) {
      const row = this.getRow(i);
      const col = this.getCol(i);
      const square = this.getSquare(Math.floor(i / 3) * 3, (i % 3) * 3);
      if (!this.isSubdivisionUnique(row) || !this.isSubdivisionUnique(col) || !this.isSubdivisionUnique(square)) {
        return false;
      }
    }
    return true;
  }

  ////////////////////////////////////////////////////////////
  //// Event Handlers
  onCellClick(row: number, col: number, event: any) {
    if (!this.canModifyCell(row, col)) return; // Do nothing if cell is not modifiable

    if (this.isCellActive(row, col)) {
      this.active_cell.value = null;
      event.srcElement.blur();

      return;
    }
    this.active_cell.value = [row, col];
    this.emit("cell-selected", { index: row * this.COLS + col });
  }

  onCellKeyDown(row: number, col: number, event: any) {
    if (this.active_cell.value === null) return; // Do nothing if no cell is active
    if (!this.canModifyCell(row, col)) return; // Do nothing if cell is not modifiable

    // If user preses escape, clear the active cell, and blur (unfocus) the currently focused cell
    if (event.key === "Escape") {
      this.active_cell.value = null;
      this.emit("cell-unselected", { index: row * this.COLS + col });
      event.srcElement.blur();
      return;
    }

    if (event.key === "Backspace") {
      this.puzzle.user_grid[row * this.COLS + col] = 0;
      this.emit("cell-cleared", { index: row * this.COLS + col });
      return;
    }

    // If user presses a number key, fill the active cell with that number
    const number = parseInt(event.key);
    if (1 <= number && number <= 9) {
      this.puzzle.user_grid[row * this.COLS + col] = number;
      this.emit("cell-number-changed", { index: row * this.COLS + col, number });
    }
  }
}

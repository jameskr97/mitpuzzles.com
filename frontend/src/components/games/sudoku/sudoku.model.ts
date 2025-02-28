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

import { type Ref, ref } from 'vue';
export class ModelSudokuPuzzle {
    readonly ROWS: number = 9;
    readonly COLS: number = 9;
    private VALID_SUBDIVISION: Set<number> = new Set([1, 2, 3, 4, 5, 6, 7, 8, 9]);

    active_cell: Ref<[number, number] | null>;
    base_grid: Ref<number[]>; // 9x9 grid
    user_grid: Ref<number[]>; // 9x9 grid


    constructor() {
        this.base_grid = ref(this.createGrid());
        this.user_grid = ref(new Array(this.ROWS * this.COLS).fill(0));
        this.active_cell = ref(null);
    }

    ////////////////////////////////////////////////////////////
    //// Game Creation + Model Request
    createGrid() {
        const b1 = JSON.parse("[1,2,3,0,5,6,7,8,0,4,5,6,7,8,9,1,2,0,7,8,9,1,2,3,4,5,6,2,1,4,0,0,5,0,9,7,3,6,5,0,9,7,2,1,4,8,9,7,2,1,4,3,6,0,5,3,1,6,4,2,9,7,8,6,4,2,9,7,8,5,3,1,9,7,0,5,3,1,6,4,2]");
        const b2 = JSON.parse("[1,0,3,4,5,6,7,0,9,4,5,6,7,0,9,1,2,0,7,8,9,1,0,3,4,5,6,2,0,4,3,6,0,8,9,7,3,6,5,8,9,0,2,1,4,8,9,7,0,1,4,0,6,5,0,0,1,6,0,0,9,7,8,6,4,2,9,7,8,5,3,1,0,7,8,5,0,0,6,0,2]");
        const b3 = JSON.parse("[1,2,0,0,0,6,0,8,9,4,0,6,0,8,0,0,2,3,0,8,9,1,2,3,0,5,6,2,1,0,3,6,0,8,9,0,0,6,0,0,0,7,2,0,4,8,9,0,2,1,4,3,6,5,5,3,1,0,0,2,9,7,8,6,0,2,9,0,8,5,3,1,0,7,0,5,3,0,0,4,2]");
        const b4 = JSON.parse("[0,0,0,4,5,6,7,0,0,4,5,0,0,8,0,1,2,3,0,8,9,0,2,3,4,0,6,2,1,4,3,0,0,8,9,7,3,0,0,0,9,7,2,1,4,0,0,0,0,1,4,3,6,5,5,0,1,0,0,2,0,7,0,0,0,2,9,0,8,0,0,0,9,7,0,5,3,0,0,0,0]");
        const b5 = JSON.parse("[1,0,0,0,0,0,7,8,9,4,0,0,7,0,9,0,2,3,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,5,0,0,0,0,0,4,8,0,0,0,0,0,3,6,5,5,0,1,6,4,2,9,7,8,6,4,2,0,0,8,5,3,0,9,0,8,5,3,0,0,4,0]");
        const b6 = JSON.parse("[1,0,0,0,5,0,7,0,0,0,0,0,0,0,0,0,0,0,7,0,0,0,0,0,4,0,6,0,1,4,3,6,5,0,0,7,0,0,5,8,0,7,2,1,4,0,9,0,0,0,0,0,0,5,0,3,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,1,9,0,0,0,3,0,6,4,0]");
        return b2;
    }

    canModifyCell = (row: number, col: number) => this.base_grid.value[row * this.COLS + col] === 0;

    isSquareSelected = (row: number, col: number) => {
        if (this.active_cell.value === null) return false;
        const [active_row, active_col] = this.active_cell.value;
        return Math.floor(active_row / 3) === Math.floor(row / 3) && Math.floor(active_col / 3) === Math.floor(col / 3);
    }

    isRowSelected = (row: number) => this.active_cell.value && this.active_cell.value[0] === row;
    isColSelected = (col: number) => this.active_cell.value && this.active_cell.value[1] === col;

    isCellActive = (row: number, col: number) => this.active_cell.value && this.active_cell.value[0] === row && this.active_cell.value[1] === col;
    getCellDisplay(row: number, col: number) {
        const index = row * this.COLS + col;
        if (this.base_grid.value[index] !== 0)
            return this.base_grid.value[index];

        const user_value = this.user_grid.value[index];
        return user_value === 0 ? ' ' : user_value;
    }

    ////////////////////////////////////////////////////////////
    //// Grid Subdivision
    getRow = (row: number) => this.base_grid.value.slice(row * this.COLS, row * this.COLS + this.COLS);
    getCol = (col: number) => this.base_grid.value.filter((_, i) => i % this.COLS === col);
    getSquare = (row: number, col: number) => {
        const startRow = Math.floor(row / 3) * 3;
        const startCol = Math.floor(col / 3) * 3;
        const square = [];
        for (let i = startRow; i < startRow + 3; i++) {
            for (let j = startCol; j < startCol + 3; j++) {
                square.push(this.base_grid.value[i * this.COLS + j]);
            }
        }
        return square;
    }

    ////////////////////////////////////////////////////////////
    //// Game Logic
    isSubdivisionUnique = (subdivision: number[]): boolean => new Set(subdivision).size === subdivision.length;

    ////////////////////////////////////////////////////////////
    //// Event Handlers
    onCellClick(row: number, col: number, event: any) {
        if(!this.canModifyCell(row, col)) return; // Do nothing if cell is not modifiable

        if (this.isCellActive(row, col)) {
            this.active_cell.value = null;
            event.srcElement.blur();

            return;
        }
        this.active_cell.value = [row, col];
    }

    onCellKeyDown(row: number, col: number, event: any) {
        if(this.active_cell.value === null) return; // Do nothing if no cell is active
        if(!this.canModifyCell(row, col)) return; // Do nothing if cell is not modifiable

        // If user preses escape, clear the active cell, and blur (unfocus) the currently focused cell
        if (event.key === 'Escape'){
            this.active_cell.value = null;
            event.srcElement.blur();
            return;
        }

        if (event.key === 'Backspace') {
            this.user_grid.value[row * this.COLS + col] = 0;
            return;
        }

        // If user presses a number key, fill the active cell with that number
        const number = parseInt(event.key);
        if (1 <= number && number <= 9) {
            this.user_grid.value[row * this.COLS + col] = number;
        }
    }

}
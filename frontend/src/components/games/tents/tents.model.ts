import { type Ref, ref } from 'vue';


export class ModelTentsPuzzle {
    readonly ROWS: number;
    readonly COLS: number;

    top_numbers: number[];
    left_numbers: number[];
    readonly grid_trees: number[];
    grid_tents: Ref<number[]>;

    constructor() {
        this.ROWS = 6;
        this.COLS = 6;
        this.top_numbers = [2, 0, 2, 0, 1, 2];
        this.left_numbers = [1, 1, 1, 2, 0, 2];
        this.grid_trees = [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0];
        this.grid_tents = ref(new Array(this.ROWS * this.COLS).fill(0));
    }

    ////////////////////////////////////////////////////////////
    //// Game Creation + Model Request
    isCellTree = (row: number, col: number) => this.grid_trees[row * this.COLS + col] === 1;
    isCellTent = (row: number, col: number) => this.grid_tents.value[row * this.COLS + col] === 1;
    getTopNumber = (col: number) => this.top_numbers[col];
    getLeftNumber = (row: number) => this.left_numbers[row];

    // return true if the cell is next to a tree horizontally, vertically, or diagonally
    isCellAdjacentToTent = (row: number, col: number) => {
        const neighbors = this.getNeighboringCells(row, col);
        neighbors.push([row, col]); // include the current cell
        for (const [r, c] of neighbors) {
            if (this.grid_tents.value[r * this.COLS + c] === 1) {
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
    onCellClick(row: number, col: number) {
        const index = row * this.COLS + col;
        if (this.grid_trees[index] === 1) return;


        // if we click on a tent, remove it
        if (this.grid_tents.value[index] === 1) {
            this.grid_tents.value[index] = 0;
            return;
        }
        // invariant - we are clicking on an empty cell
        // check if a cell is adjacent to a tree
        // prevent placing a tent if it's adjacent to a tent
        console.log('checking')
        const neighbors = this.getNeighboringCells(row, col);
        for (const [r, c] of neighbors) {
            if (this.grid_tents.value[r * this.COLS + c] === 1) {
                return;
            }
        }

        // place the tent
        this.grid_tents.value[index] = 1;

    }
}
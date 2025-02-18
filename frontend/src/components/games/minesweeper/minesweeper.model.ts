import { ref } from 'vue';

/**
 * Manages the visual state of the minesweeper board.
 * Must be stored in a reactive variable to update the view when the state changes.
 */
export class ModelMinesweeperPuzzle {
    // Possible states of a cell (U: unrevealed, F: flag, S: safe)
    private readonly CELL_CYCLE_ORDER: string[] = ["U", "F", "S"];

    // Board Game Info
    private board: string[];
    private rows: number;
    private cols: number;

    // Danger Cell + Zone
    private danger_zone_active: boolean; // Whether the danger cell is currently being held down
    private danger_zone: [number, number][]; // The cells surrounding the danger cell

    constructor(rows: number, cols: number, board: string) {
        console.log(board)
        this.rows = rows;
        this.cols = cols;
        this.board = board.split("");

        this.danger_zone = [];
        this.danger_zone_active = false;
    }

    ////////////////////////////////////////////////////////////
    //// Getters, Setters, Helpers

    /**
     * Get the class of a cell based on its content.
     * @returns the class of the cell
     */
    getCellClass(row: number, col: number): string {
        const index = row * this.cols + col;
        const cell_count = Number(this.board[index]); // this may be NaN, because board has letters

        // If it is a number, return the cell class for the number
        if (this.isCellNumeric(index)) return "cell-0" + cell_count;
        if (this.board[index] === "F") return "cell-flag";
        if (this.board[index] === "S") return "cell-00";
        if (this.board[index] === "U") {
            // If we're in the danger zone, and the zone is active
            if(this.danger_zone_active && this.danger_zone.some(([r, c]) => r === row && c === col))
                return "cell-00";
            return "cell-unrevealed";
        }

        // Show as unrevealed as default.
        return "cell-unrevealed";
    }

    getNeighboringCells(row: number, col: number): [number, number][] {
        const neighbors: [number, number][] = [];

        // -1 to 1 inclusive so we can just add the offset to the current row/col
        for (let i = -1; i <= 1; i++) {
            for (let j = -1; j <= 1; j++) {
                const newRow = row + i;
                const newCol = col + j;
                if (row >= 0 && row < this.rows && col >= 0 && col < this.cols) {
                    neighbors.push([newRow, newCol]);
                }
            }
        }
        return neighbors;
    }

    isCellNumeric(index: number): boolean {
        return !isNaN(Number(this.board[index]));
    }

    /**
     * Cycle between possible states of a cell after each click.
     * Cycle order defined in
     * @param row
     * @param col
     */
    cycleCellState(row: number, col: number): void {
        const index = row * this.cols + col;
        if(!isNaN(Number(this.board[index]))) return; // Do not cycle if cell is a number

        const cell_state = this.board[index];
        const next_state = this.CELL_CYCLE_ORDER[(this.CELL_CYCLE_ORDER.indexOf(cell_state) + 1) % this.CELL_CYCLE_ORDER.length];
        this.board[index] = next_state;
    }

    /**
     * Show or clear the area around the cell that is currently being held down.
     * (Only works if the cell is a number)
     * @param row
     * @param col
     */
    showDangerZone(event: MouseEvent, row: number, col: number): void {
        const index = row * this.cols + col;
        if (!this.isCellNumeric(index)) return;
        // invariant - cell is a number, show danger zone
        if(event.buttons === 1) {
            this.danger_zone = this.getNeighboringCells(row, col);
        }

    }

    ////////////////////////////////////////////////////////////
    //// Actions

    /** Event called when a cell is hovered over */
    onCellMouseEnter(row: number, col: number): void {
        this.danger_zone = this.getNeighboringCells(row, col);
    }

    /** Event when the user clicks on a cell */
    onCellMouseDown(row: number, col: number): void {
        if (this.isCellNumeric(row * this.cols + col)) {
            this.danger_zone_active = true;
        }
    }

    /** Event when user releases mouse on a cell */
    onCellMouseUp(row: number, col: number): void {
        // Deactive danger mode
        this.danger_zone_active = false;

        if (!this.isCellNumeric(row * this.cols + col)) {
            this.cycleCellState(row, col);
            return;
        }

        // invariant - user released mounse on a number cell
        // check if surrounding flagged cells match the number
        const index = row * this.cols + col;
        const cell_count = Number(this.board[index]);
        const neighbors = this.getNeighboringCells(row, col);
        const flagged_neighbors = neighbors.filter(([r, c]) => this.board[r * this.cols + c] === "F");
        // if true, flag in danger zone == number the user clicked on
        if (flagged_neighbors.length === cell_count) {
            // get all neighbors that are unrevealed
            const unrevealed_neighbors = neighbors.filter(([r, c]) => this.board[r * this.cols + c] === "U")

            // mark then as unrevealed
            unrevealed_neighbors.forEach(([r, c]) => this.board[r * this.cols + c] = "S");
        }
    }
}

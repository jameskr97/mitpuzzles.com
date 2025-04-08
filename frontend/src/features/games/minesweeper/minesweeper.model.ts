export enum MinesweeperCellStates {
  Unmarked = 0,
  Flagged,
  Safe,
  NUM_STATES,
}

export interface MinesweeperState {
  rows: number;
  cols: number;
  board: number[]; // immutable clues (0‑8, U/F/S already mapped)
  gamestate: number[]; // mutable player marks
  completed_at: number | null;
}

type EmitCallback = (event: string, payload?: any) => void;

/**
 * Manages the visual state of the minesweeper board.
 * Must be stored in a reactive variable to update the view when the state changes.
 */
export class ModelMinesweeperPuzzle {
  readonly ROWS: number;
  readonly COLS: number;

  // Danger Cell + Zone
  public danger_zone_active: boolean; // Whether the danger cell is currently being held down
  public danger_zone: [number, number][]; // The cells surrounding the danger cell

  // Event Tracking
  private HOVER_TIME_MINIMUM: number = 2000; // ms
  private hover_enter_time?: number;

  /**
   * @param puzzle The puzzle state
   * @param emit The emit function to call when the state changes
   */
  constructor(
    private puzzle: MinesweeperState,
    private emit: EmitCallback,
  ) {
    this.ROWS = puzzle.rows;
    this.COLS = puzzle.cols;
    this.danger_zone = [];
    this.danger_zone_active = false;
  }

  private idx = (row: number, col: number) => row * this.COLS + col;

  ////////////////////////////////////////////////////////////
  //// Getters, Setters, Helpers
  getCellBoard = (row: number, col: number): number => this.puzzle.board[this.idx(row, col)];
  getCellState = (row: number, col: number): MinesweeperCellStates => this.puzzle.gamestate[this.idx(row, col)];
  getCellNumber = (row: number, col: number): number => this.puzzle.board[this.idx(row, col)];
  isCellFlagged = (row: number, col: number): boolean =>
    !this.isCellNumeric(this.idx(row, col)) &&
    this.puzzle.gamestate[this.idx(row, col)] === MinesweeperCellStates.Flagged;
  isCellSafe = (row: number, col: number): boolean =>
    !this.isCellNumeric(this.idx(row, col)) && this.puzzle.gamestate[this.idx(row, col)] === MinesweeperCellStates.Safe;

  isCellUnmarked(row: number, col: number): boolean {
    return (
      !this.isCellNumeric(this.idx(row, col)) &&
      this.puzzle.gamestate[this.idx(row, col)] === MinesweeperCellStates.Unmarked &&
      !this.isCellInDangerZone(row, col)
    );
  }

  /**
   * Check conditions of the given cell to determine if the cell should appear as a danger cell.
   * @param row Row of the cell
   * @param col Column of the cell
   * @returns
   */
  isCellInDangerZone(row: number, col: number): boolean {
    // Danger zone
    const cond1 = !this.isCellNumeric(this.idx(row, col)) && !this.isCellFlagged(row, col);
    const cond2 = this.danger_zone_active; // Danger zone should be active
    const cond3 = this.danger_zone.some(([r, c]) => r === row && c === col); // Cell should be in the danger zone
    const cond4 = !this.isCellSafe(row, col); // Safe cells should not be in the danger zone
    return cond1 && cond2 && cond3 && cond4;
  }

  /**
   * Get the class of a cell based on its content.
   * @returns the class of the cell
   */
  getCellClass(row: number, col: number): string {
    const index = this.idx(row, col);
    const cell_val = this.puzzle.board[index];
    if (this.isCellNumeric(index)) return "cell-0" + cell_val;

    if (this.puzzle.gamestate[index] === MinesweeperCellStates.Flagged) return "cell-flag";
    if (this.puzzle.gamestate[index] === MinesweeperCellStates.Safe) return "cell-safe";
    if (this.puzzle.gamestate[index] === MinesweeperCellStates.Unmarked) {
      // If we're in the danger zone, and the zone is active
      if (this.danger_zone_active && this.danger_zone.some(([r, c]) => r === row && c === col)) return "cell-empty";
      return "cell-unrevealed";
    }

    // Show as unrevealed as default.
    return "cell-empty";
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

  /**
   * Should the cell at the given index be a visible 0-8 number?
   * @param index
   * @returns True if we want to see a number, false if another state
   */
  isCellNumeric(index: number): boolean {
    const x = this.puzzle.board[index];
    return 0 <= x && x <= 8;
  }

  /**
   * Cycle between possible states of a cell after each click.
   * Cycle order defined in
   * @param row
   * @param col
   */
  cycleCellState(row: number, col: number): void {
    const index = this.idx(row, col);
    if (this.isCellNumeric(index)) return; // Do not cycle if cell is a number

    // Get current state
    const cell_state_value = this.puzzle.gamestate[index];

    // Wrap around + save to the next state
    this.puzzle.gamestate[index] = (cell_state_value + 1) % MinesweeperCellStates.NUM_STATES;

    // TODO: Ensure the emitted events match the defineEmits in the minesweeper.puzzle.vue
    switch (this.puzzle.gamestate[index]) {
      case MinesweeperCellStates.Flagged:
        this.emit("cell-flagged", { index });
        break;
      case MinesweeperCellStates.Safe:
        this.emit("cell-safe", { index });
        break;
      case MinesweeperCellStates.Unmarked:
        this.emit("cell-unrevealed", { index });
        break;
    }
  }

  /**
   * Show or clear the area around the cell that is currently being held down.
   * (Only works if the cell is a number)
   * @param row
   * @param col
   */
  showDangerZone(event: MouseEvent, row: number, col: number): void {
    const index = this.idx(row, col);
    if (!this.isCellNumeric(index)) return;
    // invariant - cell is a number, show danger zone
    if (event.buttons === 1) {
      this.danger_zone = this.getNeighboringCells(row, col);
    }
  }

  ////////////////////////////////////////////////////////////
  //// Actions
  onCellMouseEnter(row: number, col: number): void {
    // if(this.puzzle.completed_at) return;

    if (!this.isCellNumeric(this.idx(row, col))) return;
    this.danger_zone = this.getNeighboringCells(row, col);
    this.hover_enter_time = Date.now();
  }

  onCellMouseLeave(row: number, col: number): void {
    // if(this.puzzle.completed_at) return;
    const time_leave = Date.now();
    if (this.hover_enter_time === undefined) return;
    const time_diff = time_leave - this.hover_enter_time;
    if (time_diff < this.HOVER_TIME_MINIMUM) return;

    const index = this.idx(row, col);
    this.emit("cell-hovered", { index: index, hover_time: time_diff });
  }

  /** Event when the user clicks on a cell */
  onCellMouseDown(row: number, col: number): void {
    // if(this.puzzle.completed_at) return;

    if (this.isCellNumeric(this.idx(row, col))) {
      this.danger_zone_active = true;
    }
  }

  /** Event when user releases mouse on a cell */
  onCellMouseUp(row: number, col: number): void {
    // if(this.puzzle.completed_at) return;

    const index = this.idx(row, col);

    // Deactive danger mode
    this.danger_zone_active = false;

    if (!this.isCellNumeric(index)) {
      this.cycleCellState(row, col);
      return;
    }
    // invariant applies (validated above) - user released mouse on a number cell

    // check if surrounding flagged cells match the number
    const cell_value = this.getCellBoard(row, col); // (row,col) value (guranteed from above invariant)

    const neighbors = this.getNeighboringCells(row, col);
    const flagged_neighbors = neighbors.filter(
      ([row, col]) => this.getCellState(row, col) === MinesweeperCellStates.Flagged,
    );

    // only continue if the number of flagged neighbors matches the cell value
    if (flagged_neighbors.length !== cell_value) return;

    // get unrevealed neighbors
    const unrevealed_neighbors = neighbors.filter(
      ([row, col]) =>
        this.getCellState(row, col) === MinesweeperCellStates.Unmarked && !this.isCellNumeric(this.idx(row, col)),
    );

    // mark them as unrevealed
    const touched: number[] = [];
    unrevealed_neighbors.forEach(([r, c]) => {
      const index = r * this.COLS + c;
      this.puzzle.gamestate[index] = MinesweeperCellStates.Safe;
      touched.push(index);
    });

    // emit the event
    if (touched.length === 0) return;
    this.emit("zone-cleared", { index, touched });
  }

  onGridLeave(): void {
    this.danger_zone_active = false;
  }
}

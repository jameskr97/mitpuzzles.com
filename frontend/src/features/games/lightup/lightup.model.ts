enum LightupCellStates {
  Wall0 = 0,
  Wall1 = 1,
  Wall2 = 2,
  Wall3 = 3,
  Wall4 = 4,
  WallBlank = 5,
  Empty = 6,
  Bulb = 7,
}

export interface LightupState {
  rows: number;
  cols: number;
  walls: number[];
  lit: number[];
  bulbs: number[];
}

type EmitCallback = (event: string, payload?: any) => void;
export class ModelLightupPuzzle {
  readonly ROWS: number;
  readonly COLS: number;
  private readonly WALL_NUMBERS = [
    LightupCellStates.Wall0,
    LightupCellStates.Wall1,
    LightupCellStates.Wall2,
    LightupCellStates.Wall3,
    LightupCellStates.Wall4,
    LightupCellStates.WallBlank,
  ];

  constructor(
    public puzzle: LightupState,
    public emits: EmitCallback,
  ) {
    this.ROWS = this.puzzle.rows;
    this.COLS = this.puzzle.cols;
  }

  ////////////////////////////////////////////////////////////
  //// Game Creation + Model Request
  idx = (row: number, col: number): number => row * this.COLS + col;

  isWall(row: number, col: number): boolean {
    return this.WALL_NUMBERS.includes(this.puzzle.walls[this.idx(row, col)]);
  }

  isBulb(row: number, col: number): boolean {
    return this.puzzle.bulbs[this.idx(row, col)] === 1;
  }

  isLit(row: number, col: number): boolean {
    return this.puzzle.lit[this.idx(row, col)] === 1;
  }

  canModifyCell(row: number, col: number): boolean {
    if (this.isWall(row, col)) return false;
    return true;
  }

  update_lit_cells() {
    // reset lit array to bulb locations (if a bulb is present, being lit is implied)
    for (let i = 0; i < this.puzzle.lit.length; i++) this.puzzle.lit[i] = 0;

    // mark cardinal direction deltas
    const directions = [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1],
    ];

    for (let row = 0; row < this.ROWS; row++) {
      for (let col = 0; col < this.COLS; col++) {
        const i = this.getIndex(row, col);
        if (this.puzzle.bulbs[i] !== 1) continue; // skip if not a bulb

        for (const [dy, dx] of directions) {
          let r = row + dy;
          let c = col + dx;

          // while we are in bounds and not hitting a wall
          while (r >= 0 && r < this.ROWS && c >= 0 && c < this.COLS) {
            if (this.isWall(r, c)) break;
            if (this.isBulb(r, c)) break;
            this.puzzle.lit[this.getIndex(r, c)] = 1;

            r += dy;
            c += dx;
          }
        }
      }
    }
  }

  getIndex(row: number, col: number): number {
    return row * this.COLS + col;
  }

  getWallNumber(row: number, col: number): string {
    const num = this.puzzle.walls[row * this.COLS + col];
    if (0 <= num && num <= 4) return String(num);
    return "";
  }

  ////////////////////////////////////////////////////////////
  //// Event Handlers
  onCellClick(row: number, col: number) {
    if (!this.canModifyCell(row, col)) return;

    this.puzzle.bulbs[this.idx(row, col)] = Number(!this.isBulb(row, col));
    this.update_lit_cells();

    this.emits("cell-changed", {
      index: this.idx(row, col),
      has_bulb: Boolean(this.puzzle.bulbs[this.idx(row, col)]),
    });
  }
}

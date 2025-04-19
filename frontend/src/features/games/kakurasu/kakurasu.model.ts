export enum KakurasuCellStates {
  Empty = 0,
  Filled = 1,
  Crossed = 2,
  NUM_STATES,
}
function cellStateAsString(state: number): string {
  if (state === KakurasuCellStates.Empty) return "empty";
  if (state === KakurasuCellStates.Filled) return "filled";
  if (state === KakurasuCellStates.Crossed) return "crossed";
  return "unknown";
}

export interface KakurasuState {
  cols: number;
  rows: number;
  col_sum: number[];
  row_sum: number[];
  cell_black: number[];
}

type EmitCallback = (event: string, payload?: any) => void;
export class ModelKakurasuPuzzle {
  readonly ROWS: number;
  readonly COLS: number;

  constructor(
    public store: KakurasuState,
    private emit: EmitCallback,
  ) {
    this.ROWS = store.rows;
    this.COLS = store.cols;
  }

  getCellState(row: number, col: number): number {
    return this.store.cell_black[row * this.COLS + col];
  }

  getRowSum(row: number): number {
    let sum = 0;
    for (let i = 0; i < this.COLS; i++) {
      if (this.getCellState(row, i) === KakurasuCellStates.Filled) {
        sum += i + 1;
      }
    }
    return sum;
  }

  getColSum(col: number): number {
    let sum = 0;
    for (let i = 0; i < this.ROWS; i++) {
      if (this.getCellState(i, col) === KakurasuCellStates.Filled) {
        sum += i + 1;
      }
    }
    return sum;
  }

  onCellClick(row: number, col: number, event: MouseEvent): void {
    const index = row * this.COLS + col;
    const state = this.store.cell_black[index];

    // go backwards if right click
    if (event.button === 2) {
      this.store.cell_black[index] = (state + KakurasuCellStates.NUM_STATES - 1) % KakurasuCellStates.NUM_STATES;
    } else {
      this.store.cell_black[index] = (state + 1) % KakurasuCellStates.NUM_STATES;
    }

    // Emit the event to update the store
    this.emit("cell-changed", { index, cell_state: cellStateAsString(this.store.cell_black[index]) });
  }
}

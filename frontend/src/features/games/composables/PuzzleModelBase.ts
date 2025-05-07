import type { Ref } from "vue";
import { toRef } from "vue";
import type { MutablePuzzleState, PuzzleStateSudoku } from "@/services/states.ts";
import { useCellStateCycler } from "@/features/games/composables/useCellStateCycler.ts";
import { useHoverTracking } from "@/features/games/composables/useHoverTracking.ts";
import { useSudokuHighlight } from "@/features/games/composables/useSudokuHighlight.ts";

type EmitCallback = (event: string, payload?: any) => void;

export interface PuzzleModelHooks<T extends MutablePuzzleState> {
  allowedStates?: number[];
  canModifyCell?: (row: number, col: number, state: T) => boolean;
  onCellClick?: (row: number, col: number, state: T) => void;
  onCellHoverThreshold?: (row: number, col: number, time: number, state: T) => void;
  onCellMouseEnter?: (row: number, col: number, state: T) => void;
  onCellMouseLeave?: (row: number, col: number, state: T) => void;
  onClickRow?: (row: number, state: T) => void;
  onClickCol?: (col: number, state: T) => void;
}

export interface PuzzleModel<T extends MutablePuzzleState> {
  rows: Ref<number>;
  cols: Ref<number>;
  state: Ref<T>;
  index(row: number, col: number): number;

  getCellState(row: number, col: number): number;
  onCellClick?(row: number, col: number, event: MouseEvent): void;
  onCellMouseDown?(row: number, col: number, event: MouseEvent): void;
  onCellMouseUp?(row: number, col: number, event: MouseEvent): void;
  onCellMouseEnter?(row: number, col: number): void
  onCellMouseLeave?(row: number, col: number): void;
  onCellKeyDown?(row: number, col: number, event: KeyboardEvent): void;
  onCellKeyUp?(row: number, col: number, event: KeyboardEvent): void;
  onRowClick?(row: number): void;
  onColClick?(col: number): void;
}

export function createStateMachinePuzzleModel<T extends MutablePuzzleState>(
  stateRef: Ref<T>,
  NUM_STATES: number,
  _emit: EmitCallback,
  hooks?: PuzzleModelHooks<T>,
): PuzzleModel<T> {
  // Composition Components
  const cycler = useCellStateCycler(NUM_STATES, hooks?.allowedStates);
  const hover = useHoverTracking();

  function index(row: number, col: number): number {
    return row * stateRef.value.cols + col;
  }

  return {
    rows: toRef(stateRef.value, "rows"),
    cols: toRef(stateRef.value, "cols"),
    state: toRef(stateRef),
    index,

    getCellState(row: number, col: number): number {
      const indexVal = index(row, col);
      return stateRef.value.board[indexVal];
    },
    onCellClick(row: number, col: number, event: MouseEvent) {
      const indexVal = index(row, col);
      const state = stateRef.value.board[indexVal];

      // Check if the cell can be modified
      const canModify = hooks?.canModifyCell?.(row, col, stateRef.value) ?? true; // Default: modifiable
      if (!canModify) return;

      stateRef.value.board[indexVal] = cycler.cycle(state, event.button);
      hooks?.onCellClick?.(row, col, stateRef.value);
    },
    onCellMouseEnter(row: number, col: number) {
      hover.onMouseEnter();
      hooks?.onCellMouseEnter?.(row, col, stateRef.value);
    },
    onCellMouseLeave(row, col) {
      hover.onMouseLeave((time) => hooks?.onCellHoverThreshold?.(row, col, time, stateRef.value));
      hooks?.onCellMouseLeave?.(row, col, stateRef.value);
    },
    onRowClick(row: number) {
      hooks?.onClickRow?.(row, stateRef.value);
    },
    onColClick(col: number) {
      hooks?.onClickCol?.(col, stateRef.value);
    },
  };
}

export interface PuzzleModelSudoku extends PuzzleModel<PuzzleStateSudoku> {
  highlight: ReturnType<typeof useSudokuHighlight>;
  getCellValue(row: number, col: number): string;
  isCellActive(row: number, col: number): boolean;
  canModifyCell(row: number, col: number): boolean;
}

export function createSudokuPuzzleModel(
  stateRef: Ref<PuzzleStateSudoku>,
  _hooks?: PuzzleModelHooks<PuzzleStateSudoku>,
): PuzzleModelSudoku {
  // TODO(james): This highlighter assumes a square board
  const highlight = useSudokuHighlight(stateRef, stateRef.value.rows);

  function index(row: number, col: number): number {
    return row * stateRef.value.cols + col;
  }

  return {
    rows: toRef(stateRef.value, "rows"),
    cols: toRef(stateRef.value, "cols"),
    state: toRef(stateRef),
    index,
    highlight,

    getCellState(row: number, col: number): number {
      return stateRef.value.board[row * stateRef.value.cols + col];
    },

    onCellClick(row: number, col: number, _event: MouseEvent) {
      if (!this.canModifyCell(row, col)) return;
      stateRef.value.active_cell = [row, col];
    },

    getCellValue(row: number, col: number): string {
      const index = row * stateRef.value.cols + col;

      if (stateRef.value.board_initial[index] !== "0") return stateRef.value.board_initial[index];
      const user_value = stateRef.value.board[index];
      return user_value === 0 ? " " : String(user_value);
    },

    onCellKeyDown(row: number, col: number, event: KeyboardEvent) {
      const index = row * stateRef.value.cols + col;
      const key = event.key;

      const isFixed = stateRef.value.board_initial[index] !== "0";
      if (isFixed) return; // Can't modify initial clues.

      if (key >= "1" && key <= "9") stateRef.value.board[index] = parseInt(key);
      if (key === "Backspace" || key === "Delete") stateRef.value.board[index] = 0;
    },

    isCellActive(row: number, col: number): boolean {
      if (stateRef.value.active_cell === undefined) return false;
      const [activeRow, activeCol] = stateRef.value.active_cell;
      return activeRow === row && activeCol === col;
    },

    canModifyCell(row: number, col: number): boolean {
      return stateRef.value.board_initial[row * stateRef.value.cols + col] === "0";
    },
  };
}

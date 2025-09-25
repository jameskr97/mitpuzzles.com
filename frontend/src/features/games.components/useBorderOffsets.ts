import { computed } from "vue";
import type { BoardContext } from "@/features/games.components/board.ts";

/**
 * Calculates the border offsets for both the game grid and gutters.
 *
 * - gameInnerBorderOffsetsX/Y: Offsets between each column/row inside the main game grid,
 *   accounting for variable border thickness from the borderConfig.
 *
 * - uniformBorderOffsetX/Y: Offsets used for gutters, assuming uniform gaps (ignores borderConfig).
 *   Used for vertical gaps on the left and right, and horizontal gaps on the top and bottom.
 *
 * This composable is intended to provide the pixel positions for cells and gutters
 * when rendering the board layout.
 */
export function useBorderOffsets(board: BoardContext) {
  const gameInnerBorderOffsetsX = computed(() => {
    const offsets = [0];
    const maxCols = Math.max(board.cols, board.gutters.left, board.gutters.right);
    for (let c = 1; c < maxCols; c++) {
      const prev = offsets[c - 1];

      // determine thickness for the column c
      const defaultThickness = board.gap;
      const nth = board.borderConfig.everyNthCol;
      const nthThickness = nth && c % nth.n === 0 ? (nth.style.thickness ?? defaultThickness) : undefined;
      const colSpecific = board.borderConfig?.cols?.[c]?.thickness;
      const thickness = colSpecific ?? nthThickness ?? defaultThickness;
      offsets.push(prev + board.cellSize + thickness);
    }
    return offsets;
  });

  const gameInnerBorderOffsetsY = computed(() => {
    const offsets = [0];
    const maxRows = Math.max(board.rows, board.gutters.top, board.gutters.bottom);
    for (let r = 1; r < maxRows; r++) {
      const prev = offsets[r - 1];

      // determine row thickness for the row r
      const defaultThickness = board.gap;
      const nth = board.borderConfig.everyNthRow;
      const nthThickness = nth && r % nth.n === 0 ? (nth.style.thickness ?? defaultThickness) : undefined;
      const rowSpecific = board.borderConfig?.rows?.[r]?.thickness;
      const thickness = rowSpecific ?? nthThickness ?? defaultThickness;

      offsets.push(prev + board.cellSize + thickness);
    }
    return offsets;
  });

  /**
   * Uniform Border Offsets
   *
   * This is for the top/bottom/left/right gutters.
   * While the gutters match the game grid spacing along parallel axes,
   * they always use uniform spacing along their independent axes (ignoring borderConfig).
   *
   * | Gutter  | Matches Game Grid Spacing On | Uses Uniform Spacing On |
   * |---------|------------------------------|-------------------------|
   * | Top     | Columns                      | Rows                    |
   * | Bottom  | Columns                      | Rows                    |
   * | Left    | Rows                         | Columns                 |
   * | Right   | Rows                         | Columns                 |
   */
  const uniformOffsets = computed(() => {
    const offsets = [0];
    const defaultThickness = board.gap;
    const maxCount = Math.max(
      board.rows,
      board.cols,
      board.gutters.top,
      board.gutters.bottom,
      board.gutters.left,
      board.gutters.right,
    );
    for (let i = 1; i <= maxCount; i++) {
      offsets.push(offsets[i - 1] + board.cellSize + defaultThickness);
    }
    return offsets;
  });

  return {
    gameInnerBorderOffsetsX,
    gameInnerBorderOffsetsY,
    uniformOffsets,
  };
}

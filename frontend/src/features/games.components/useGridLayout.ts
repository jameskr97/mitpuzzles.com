import { computed } from "vue";
import type { BoardContext } from "@/features/games.components/board.ts";
import { useBorderOffsets } from "@/features/games.components/useBorderOffsets.ts";

/**
 * Calculates the overall board layout dimensions and the position of each cell.
 *
 * Uses the offsets computed by useBorderOffsets to determine:
 * - boardWidth and boardHeight: The total pixel dimensions of the game grid.
 * - cellPosition(row, col): The pixel position and size for a given cell in the grid.
 *
 * This composable is responsible for translating row/column indices into pixel positions
 * for rendering.
 */
export function useGridLayout(board: BoardContext) {
  const offsets = useBorderOffsets(board);
  const layout = useGridPositions(board);

  // Booleans to determine if the gutter is present
  const has_top_gutter = computed(() => board.gutters.top > 0);
  const has_left_gutter = computed(() => board.gutters.left > 0);
  const has_right_gutter = computed(() => board.gutters.right > 0);
  const has_bottom_gutter = computed(() => board.gutters.bottom > 0);

  ////////////////////////////////////////////////////////////////////////////////
  ////////// Game Board Width and height (w/ borders, w/o gutters)
  const gameGridWidth = computed(() => offsets.gameInnerBorderOffsetsX.value[board.cols - 1] + board.cellSize);
  const gameGridHeight = computed(() => offsets.gameInnerBorderOffsetsY.value[board.rows - 1] + board.cellSize);

  function cellPositionGame(row: number, col: number) {
    return {
      left: layout.gameGridStartX.value + offsets.gameInnerBorderOffsetsX.value[col] + "px",
      top: layout.gameGridStartY.value + offsets.gameInnerBorderOffsetsY.value[row] + "px",
      width: board.cellSize + "px",
      height: board.cellSize + "px",
    };
  }

  function cellPositionGutterTop(row: number, col: number) {
    return {
      left: layout.topGutterStartX.value + offsets.gameInnerBorderOffsetsX.value[col] + "px",
      top: offsets.uniformOffsets.value[row] + "px",
      width: board.cellSize + "px",
      height: board.cellSize + "px",
    };
  }

  function cellPositionGutterLeft(row: number, col: number) {
    return {
      left: layout.leftGutterStartX.value + offsets.uniformOffsets.value[col] + "px",
      top: layout.leftGutterStartY.value + offsets.gameInnerBorderOffsetsY.value[row] + "px",
      width: board.cellSize + "px",
      height: board.cellSize + "px",
    };
  }
  function cellPositionGutterRight(row: number, col: number) {
    return {
      left: layout.rightGutterStartX.value + offsets.uniformOffsets.value[col] + "px",
      top: layout.rightGutterStartY.value + offsets.gameInnerBorderOffsetsY.value[row] + "px",
      width: board.cellSize + "px",
      height: board.cellSize + "px",
    };
  }

  function cellPositionGutterBottom(row: number, col: number) {
    return {
      left: layout.bottomGutterStartX.value + offsets.gameInnerBorderOffsetsX.value[col] + "px",
      top: layout.bottomGutterStartY.value + offsets.uniformOffsets.value[row] + "px",
      width: board.cellSize + "px",
      height: board.cellSize + "px",
    };
  }

  return {
    has_top_gutter,
    has_left_gutter,
    has_right_gutter,
    has_bottom_gutter,

    gameGridWidth,
    gameGridHeight,
    cellPositionGame,
    cellPositionGutterTop,
    cellPositionGutterLeft,
    cellPositionGutterRight,
    cellPositionGutterBottom,
  };
}

/**
 * Calculates the positions of the game grid and gutters based on the number of rows, columns, cell size, gap, and gutter counts.
 * It generates lists which define the starting X and Y position, based on the given columns and rows.
 * @param board
 */
export function useGridPositions(board: BoardContext) {
  const offsets = useBorderOffsets(board);

  // Calculate dimensions of each gutter + game grid
  //// game grid
  const gameGridHeight = computed(() => offsets.gameInnerBorderOffsetsY.value[board.rows - 1] + board.cellSize);
  const gameGridWidth = computed(() => offsets.gameInnerBorderOffsetsX.value[board.cols - 1] + board.cellSize);
  const gameGridOuterGap = computed(() => board.borderConfig.outer?.thickness ?? 0);
  //// top gutter
  const topGutterHeight = computed(() =>
    board.gutters.top > 0 ? board.gutters.top * (board.cellSize + board.gap) - board.gap : 0,
  );
  const topGutterWidth = gameGridWidth;
  //// left gutter
  const leftGutterWidth = computed(() =>
    board.gutters.left > 0 ? board.gutters.left * (board.cellSize + board.gap) - board.gap : 0,
  );
  const leftGutterHeight = gameGridHeight;
  //// right gutter
  const rightGutterWidth = computed(() =>
    board.gutters.right > 0 ? board.gutters.right * (board.cellSize + board.gap) - board.gap : 0,
  );
  const rightGutterHeight = gameGridHeight;
  //// bottom gutter
  const bottomGutterHeight = computed(() =>
    board.gutters.bottom > 0 ? board.gutters.bottom * (board.cellSize + board.gap) - board.gap : 0,
  );
  const bottomGutterWidth = gameGridWidth;

  // Calculate the starting position each gutter + game grid
  //// game grid
  const gameGridStartX = computed(() => leftGutterWidth.value + gameGridOuterGap.value);
  const gameGridStartY = computed(() => topGutterHeight.value + gameGridOuterGap.value);
  //// top gutter
  const topGutterStartY = computed(() => 0);
  const topGutterStartX = computed(() => gameGridStartX.value);
  //// left gutter
  const leftGutterStartX = computed(() => 0);
  const leftGutterStartY = computed(() => gameGridStartY.value);
  //// right gutter
  const rightGutterStartX = computed(() => gameGridStartX.value + gameGridWidth.value + gameGridOuterGap.value);
  const rightGutterStartY = computed(() => gameGridStartY.value);
  //// bottom gutter
  const bottomGutterStartX = computed(() => gameGridStartX.value);
  const bottomGutterStartY = computed(() => gameGridStartY.value + gameGridHeight.value + gameGridOuterGap.value);

  // Calculate the full width and height of the board
  const total_horizontal_outline = computed(() => {
    const ot = board.borderConfig.outer?.thickness ?? 0;
    const outerMostOutline = ot * 2;
    const gameGridAndLeftGutterSeparationOutline = ot * (board.gutters.left ? 1 : 0);
    const gameGridAndRightGutterSeparationOutline = ot * (board.gutters.right ? 1 : 0);
    return outerMostOutline + gameGridAndLeftGutterSeparationOutline + gameGridAndRightGutterSeparationOutline;
  });
  const total_vertical_outline = computed(() => {
    const ot = board.borderConfig.outer?.thickness ?? 0;
    const outerMostOutline = ot * 2;
    const gameGridAndTopGutterSeparationOutline = ot * (board.gutters.top ? 1 : 0);
    const gameGridAndBottomGutterSeparationOutline = ot * (board.gutters.bottom ? 1 : 0);
    return outerMostOutline + gameGridAndTopGutterSeparationOutline + gameGridAndBottomGutterSeparationOutline;
    // return ot * (board.gutters.top ? 1 : 0) + ot * (board.gutters.bottom ? 1 : 0);
  });
  const fullWidth = computed(
    () => gameGridWidth.value + leftGutterWidth.value + rightGutterWidth.value + total_horizontal_outline.value,
  );
  const fullHeight = computed(
    () => gameGridHeight.value + topGutterHeight.value + bottomGutterHeight.value + total_vertical_outline.value,
  );

  return {
    fullWidth,
    fullHeight,

    gameGridWidth,
    gameGridHeight,
    gameGridOuterGap,
    topGutterWidth,
    topGutterHeight,
    leftGutterWidth,
    leftGutterHeight,
    rightGutterWidth,
    rightGutterHeight,
    bottomGutterWidth,
    bottomGutterHeight,

    gameGridStartX,
    gameGridStartY,
    topGutterStartX,
    topGutterStartY,
    leftGutterStartX,
    leftGutterStartY,
    rightGutterStartX,
    rightGutterStartY,
    bottomGutterStartX,
    bottomGutterStartY,
  };
}

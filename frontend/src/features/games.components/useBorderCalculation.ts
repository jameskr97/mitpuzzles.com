import { type Ref, computed, type CSSProperties } from "vue";
import type { BoardContext, BorderStyle } from "@/features/games.components/board.ts";
import { useGridPositions, useGridLayout } from "@/features/games.components/useGridLayout.ts";
import { useBorderOffsets } from "@/features/games.components/useBorderOffsets.ts";

/**
 * This function is used to calculate the exact position, thickness, and dimensions of the outside
 * border of the board.
 *
 * Note: The origin point for all the border segments is the top left corner of the segment.
 */
export function useBorderCalculation(board: BoardContext) {
  const positions = useGridPositions(board);
  const offsets = useBorderOffsets(board);
  const layout = useGridLayout(board);

  const gutterBordersNS = {} as Record<
    string,
    {
      horizontal: Ref<CSSProperties>;
      left: Ref<CSSProperties>;
      right: Ref<CSSProperties>;
    }
  >;
  for (const side of ["top", "bottom"]) {
    const startX = computed(
      (): number =>
        (positions[`${side}GutterStartX` as keyof typeof positions].value as number) +
        offsets.gameInnerBorderOffsetsX.value[0],
    );
    const startY = computed(
      (): number =>
        (positions[`${side}GutterStartY` as keyof typeof positions].value as number) + offsets.uniformOffsets.value[0],
    );
    const width = computed((): number => positions[`${side}GutterWidth` as keyof typeof positions].value as number);
    const height = computed((): number => positions[`${side}GutterHeight` as keyof typeof positions].value as number);
    gutterBordersNS[side] = {
      horizontal: computed(() => ({
        left: startX.value - outsideBorderThickness.value + "px",
        top: side === "top" ? startY.value - outsideBorderThickness.value + "px" : startY.value + height.value + "px",
        width: width.value + outsideBorderThickness.value * 2 + "px",
        height: outsideBorderThickness.value + "px",
      })),
      left: computed(() => ({
        left: startX.value - outsideBorderThickness.value + "px",
        top: startY.value - outsideBorderThickness.value + "px",
        width: outsideBorderThickness.value + "px",
        height: height.value + outsideBorderThickness.value * 2 + "px",
      })),
      right: computed(() => ({
        left: startX.value + width.value + "px",
        top: startY.value - outsideBorderThickness.value + "px",
        width: outsideBorderThickness.value + "px",
        height: height.value + outsideBorderThickness.value * 2 + "px",
      })),
    };
  }

  const gutterBordersEW = {} as Record<
    string,
    {
      vertical: Ref<CSSProperties>;
      top: Ref<CSSProperties>;
      bottom: Ref<CSSProperties>;
    }
  >;

  for (const side of ["left", "right"]) {
    const startX = computed(
      (): number =>
        (positions[`${side}GutterStartX` as keyof typeof positions].value as number) + offsets.uniformOffsets.value[0],
    );
    const startY = computed(
      (): number =>
        (positions[`${side}GutterStartY` as keyof typeof positions].value as number) +
        offsets.gameInnerBorderOffsetsY.value[0],
    );
    const width = computed((): number => positions[`${side}GutterWidth` as keyof typeof positions].value as number);
    const height = computed((): number => positions[`${side}GutterHeight` as keyof typeof positions].value as number);

    gutterBordersEW[side] = {
      vertical: computed(() => ({
        top: startY.value - outsideBorderThickness.value + "px",
        left: side === "left" ? startX.value - outsideBorderThickness.value + "px" : startX.value + width.value + "px",
        width: outsideBorderThickness.value + "px",
        height: height.value + outsideBorderThickness.value * 2 + "px",
      })),
      top: computed(() => ({
        top: startY.value - outsideBorderThickness.value + "px",
        left: startX.value - outsideBorderThickness.value + "px",
        width: width.value + outsideBorderThickness.value * 2 + "px",
        height: outsideBorderThickness.value + "px",
      })),
      bottom: computed(() => ({
        ...gutterBordersEW[side].top.value,
        top: startY.value + height.value + "px",
      })),
    };
  }

  const hasOutsideBorder = computed(() => board.borderConfig.outer !== undefined);
  const outsideBorderThickness = computed(() => {
    const outerBorder = board.borderConfig.outer;
    return outerBorder?.thickness ?? 0;
  });

  const border_style_top = computed(() => ({
    // this is the border that sits on top, and we want it to start at the
    // left most edge of the left border (so the corners are not cut off)
    left: positions.gameGridStartX.value - outsideBorderThickness.value + "px",
    // origin point is top left, so we have to move it up by the thickness
    top: positions.gameGridStartY.value - outsideBorderThickness.value + "px",
    width: layout.gameGridWidth.value + 2 * outsideBorderThickness.value + "px",
    height: outsideBorderThickness.value + "px",
  }));
  const border_style_bottom = computed(() => ({
    // same as top border, but aligned just below the board
    ...border_style_top.value,
    top: positions.gameGridStartY.value + positions.gameGridHeight.value + "px",
  }));
  const border_style_left = computed(() => ({
    left: positions.gameGridStartX.value - outsideBorderThickness.value + "px",
    top: positions.gameGridStartY.value - outsideBorderThickness.value + "px",
    width: outsideBorderThickness.value + "px",
    height: layout.gameGridHeight.value + 2 * outsideBorderThickness.value + "px",
  }));
  const border_style_right = computed(() => ({
    ...border_style_left.value,
    left: positions.gameGridStartX.value + layout.gameGridWidth.value + "px",
  }));

  // Inside Border Spacing
  // This defines where the central game grid borders are placed.
  // This is affected by the borderConfig, which can define specific styles for each row/column.
  // It is to by used only by the game grid, and the LEFT + RIGHT gutters (gutter row spacing must match the game grid row spacing)
  const game_grid_borders_row = computed(() => {
    const borders = [];
    // const maxRows = Math.max(board.rows, board.gutters.top, board.gutters.bottom);
    const maxRows = board.rows;
    for (let r = 1; r < maxRows; r++) {
      // Determine if this row should get the every-Nth style
      const nth = board.borderConfig.everyNthRow;
      const nthStyle = nth && nth.n && r % nth.n === 0 ? nth.style : {};

      // Determine if this row has a specific style
      const rowSpecific = board.borderConfig.rows?.[r] || {};
      const style: BorderStyle = { ...nthStyle, ...rowSpecific };
      borders.push({ top: offsets.gameInnerBorderOffsetsY.value[r] || 0, style });
    }
    return borders;
  });

  // This defines where the central game grid borders are placed.
  // This is affected by the borderConfig, which can define specific styles for each row/column.
  // It is to by used only by the game grid, and the TOP + BOTTOM gutters (gutter column spacing must match the game grid column spacing)
  const game_grid_borders_column = computed(() => {
    const borders = [];
    // const maxCols = Math.max(board.cols, board.gutters.left, board.gutters.right);
    const maxCols = board.cols;
    for (let c = 1; c < maxCols; c++) {
      const nth = board.borderConfig.everyNthCol;
      const nthStyle = nth && nth.n && c % nth.n === 0 ? nth.style : {};
      const colSpecific = board.borderConfig.cols?.[c] || {};
      const style: BorderStyle = { ...nthStyle, ...colSpecific };
      borders.push({ left: offsets.gameInnerBorderOffsetsX.value[c] || 0, style });
    }
    return borders;
  });

  return {
    hasOutsideBorder,
    outsideBorderThickness,
    border_class: board.borderConfig.outer?.borderClass,
    border_style_top,
    border_style_bottom,
    border_style_left,
    border_style_right,
    game_grid_borders_row,
    game_grid_borders_column,

    gutterBordersNS,
    gutterBordersEW,
  };
}

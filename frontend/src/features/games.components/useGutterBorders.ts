import { computed, inject } from "vue";
import type { BoardContext } from "@/features/games.components/board.ts";
import { useBorderCalculation } from "@/features/games.components/useBorderCalculation.ts";
import { useGridPositions } from "@/features/games.components/useGridLayout.ts";
import { useBorderOffsets } from "@/features/games.components/useBorderOffsets.ts";

export function useGutterBorders(side: "top" | "bottom" | "left" | "right") {
  const board = inject<BoardContext>("boardContext")!;
  const borderCalc = useBorderCalculation(board);
  const positions = useGridPositions(board);
  const offsets = useBorderOffsets(board);

  const isTopOrBottom = side === "top" || side === "bottom";
  const rowCount = computed(() =>
    isTopOrBottom ? (side === "top" ? board.gutters.top : board.gutters.bottom) : board.rows,
  );
  const colCount = computed(() =>
    isTopOrBottom ? board.cols : side === "left" ? board.gutters.left : board.gutters.right,
  );
  const rowOffsets = computed(() =>
    isTopOrBottom ? offsets.uniformOffsets.value : offsets.gameInnerBorderOffsetsY.value,
  );
  const colOffsets = computed(() =>
    isTopOrBottom ? offsets.gameInnerBorderOffsetsX.value : offsets.uniformOffsets.value,
  );

  const borderHorizontal = computed(() => {
    if (isTopOrBottom) {
      const borders = [];
      for (let i = 1; i < rowCount.value; i++) {
        borders.push({
          top: offsets.uniformOffsets.value[i],
          style: { thickness: board.gap },
        });
      }
      return borders;
    } else {
      return borderCalc.game_grid_borders_row.value.slice(0, rowCount.value - 1);
    }
  });

  const borderVertical = computed(() => {
    if (isTopOrBottom) {
      return borderCalc.game_grid_borders_column.value.slice(0, colCount.value - 1);
    } else {
      return offsets.uniformOffsets.value.slice(1, colCount.value).map((offset, _) => ({
        left: offset,
        style: { thickness: board.gap },
      }));
    }
  });

  const startX = computed(() => positions[`${side}GutterStartX`].value);
  const startY = computed(() => positions[`${side}GutterStartY`].value);
  const width = computed(() => positions[`${side}GutterWidth`].value);
  const height = computed(() => positions[`${side}GutterHeight`].value);

  let outerBorders;
  if (isTopOrBottom) {
    outerBorders = {
      border1: borderCalc.gutterBordersNS[side].horizontal,
      border2: borderCalc.gutterBordersNS[side].left,
      border3: borderCalc.gutterBordersNS[side].right,
    };
  } else {
    outerBorders = {
      border1: borderCalc.gutterBordersEW[side].vertical,
      border2: borderCalc.gutterBordersEW[side].top,
      border3: borderCalc.gutterBordersEW[side].bottom,
    };
  }

  return {
    borderHorizontal,
    borderVertical,
    startX,
    startY,
    rowCount,
    colCount,
    rowOffsets,
    colOffsets,
    width,
    height,
    outerBorders,
  };
}

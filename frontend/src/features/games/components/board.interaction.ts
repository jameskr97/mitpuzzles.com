import { useGridLayout, useGridPositions } from "@/features/games/components/useGridLayout.ts";
import { useBorderOffsets } from "@/features/games/components/useBorderOffsets.ts";
import { useGutterBorders } from "@/features/games/components/useGutterBorders.ts";
import type { BoardContext } from "@/features/games/components/board.ts";
import type { usePuzzleModelAdapter } from "@/features/games/composables/PuzzleModelAdapter.ts";

export type GameZone = "game" | "topGutter" | "bottomGutter" | "leftGutter" | "rightGutter";
type Orientation = "horizontal" | "vertical";

type ClickedCell = { type: "cell"; row: number; col: number; zone: GameZone };
type ClickedBorder = {
  type: "border";
  orientation: Orientation;
  zone: GameZone;
  anchor: { row: number; col: number };
  direction: "top" | "bottom" | "left" | "right";
  thickness: number;
};
type HoveredCell = {
  type: "cell";
  row: number;
  col: number;
  zone: GameZone;
};

type ClickHit = ClickedCell | ClickedBorder | { type: "none" };

export class BoardInteraction {
  layout: ReturnType<typeof useGridLayout>;
  positions: ReturnType<typeof useGridPositions>;
  offset: ReturnType<typeof useBorderOffsets>;

  gutterData: {
    top: ReturnType<typeof useGutterBorders>;
    bottom: ReturnType<typeof useGutterBorders>;
    left: ReturnType<typeof useGutterBorders>;
    right: ReturnType<typeof useGutterBorders>;
  };

  // input state tracking
  private lastHover: HoveredCell | null = null;
  private focused: ClickedCell | null = null;

  constructor(
    private board: BoardContext,
    private model: ReturnType<typeof usePuzzleModelAdapter>,
  ) {
    this.layout = useGridLayout(board);
    this.positions = useGridPositions(board);
    this.offset = useBorderOffsets(board);

    this.gutterData = {
      top: useGutterBorders("top"),
      bottom: useGutterBorders("bottom"),
      left: useGutterBorders("left"),
      right: useGutterBorders("right"),
    };
  }

  // Determine if click hit something we care abot
  getHit(event: MouseEvent) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const x = (event.clientX - rect.left) / this.board.scale;
    const y = (event.clientY - rect.top) / this.board.scale;
    const res = this.findCellAt(x, y);

    if (res.type === "none") return null;
    return res;
  }

  // Event Handlers
  onMouseDown(event: MouseEvent) {
    const hit = this.getHit(event);
    if (!hit) return;
    if (hit.type === "cell") {
      this.model.onCellClick?.(hit.zone, hit.row, hit.col, event);
    } else if (hit.type === "border") {
      console.log("Border clicked:", hit);
      // this.model.onBorderClick(hit.anchor.row, hit.anchor.col, hit.zone, hit.orientation, hit.direction);
    }
  }

  onMouseUp(event: MouseEvent) {
    const hit = this.getHit(event);
    if (!hit || hit.type !== "cell") return;
    this.focused = hit;
  }

  onMouseMove(event: MouseEvent) {
    const hit = this.getHit(event);
    if (!hit) return;
    if (hit.type === "cell") {
      if (!this.lastHover || this.lastHover.row !== hit.row || this.lastHover.col !== hit.col) {
        if (this.lastHover) {
          this.model.onCellLeave?.(this.lastHover.row, this.lastHover.col);
        }
        this.model.onCellEnter?.(hit.row, hit.col);
        this.lastHover = hit;
      }
    } else if (this.lastHover) {
      this.model.onCellLeave?.(this.lastHover.row, this.lastHover.col);
      this.lastHover = null;
    }
  }

  onKeyDown(event: KeyboardEvent) {
    const hit = this.focused;
    if (!hit || hit.type !== "cell") return; // Only cells handle key events
    this.model.onCellKeyDown?.(hit.row, hit.col, event);
  }

  findCellAt(x: number, y: number): ClickHit {
    const gameHit = this.checkGameGridHit(x, y);
    if (gameHit) return gameHit;

    const gutterHit = this.checkGutterHit(x, y);
    if (gutterHit) return gutterHit;

    const borderHit = this.checkGameGridBorders(x, y);
    if (borderHit) return borderHit;

    return { type: "none" };
  }

  private checkGameGridHit(x: number, y: number): ClickHit | null {
    const { gameGridStartX, gameGridStartY } = this.positions;

    for (let row = 0; row < this.board.rows; row++) {
      // ensure we are within the row bounds
      const top = gameGridStartY.value + this.offset.gameInnerBorderOffsetsY.value[row];
      const bottom = top + this.board.cellSize;
      if (y < top || y > bottom) continue;

      for (let col = 0; col < this.board.cols; col++) {
        // ensure we are within the column bounds
        const left = gameGridStartX.value + this.offset.gameInnerBorderOffsetsX.value[col];
        const right = left + this.board.cellSize;
        if (x < left || x > right) continue;

        return { type: "cell", row, col, zone: "game" };
      }
    }
    return null;
  }

  private checkGutterHit(x: number, y: number): ClickHit | null {
    const gutters = ["top", "bottom", "left", "right"] as const;

    for (const side of gutters) {
      const data = this.gutterData[side];
      const count = this.board.gutters[side];
      if (count === 0) continue; // skip this gutter if it has no cells

      for (let r = 0; r < data.rowCount.value; r++) {
        // ensure we are within the row bounds
        const top = data.startY.value + data.rowOffsets.value[r];
        const bottom = top + this.board.cellSize;
        if (y < top || y > bottom) continue;

        for (let c = 0; c < data.colCount.value; c++) {
          // ensure we are within the column bounds
          const left = data.startX.value + data.colOffsets.value[c];
          const right = left + this.board.cellSize;
          if (x < left || x > right) continue;

          return { type: "cell", row: r, col: c, zone: `${side}Gutter` };
        }
      }
    }

    return null;
  }

  private checkGameGridBorders(x: number, y: number): ClickHit | null {
    const { gameGridStartX, gameGridStartY } = this.positions;
    const offsetY = this.offset.gameInnerBorderOffsetsY.value;
    const offsetX = this.offset.gameInnerBorderOffsetsX.value;

    // horizontal borders (between rows)
    for (let row = 1; row < this.board.rows; row++) {
      // variable thickness
      const thickness = offsetY[row] - offsetY[row - 1] - this.board.cellSize;

      // calculate vertical bounds (skip if outside bounds)
      const top = gameGridStartY.value + offsetY[row] - thickness;
      const bottom = top + thickness;
      if (y < top || y > bottom) continue;

      // calculate horizontal bounds (skip if outside bounds)
      const left = gameGridStartX.value;
      const right = left + offsetX[this.board.cols - 1] + this.board.cellSize;
      if (x < left || x > right) continue;

      const col = Math.floor((x - gameGridStartX.value) / (this.board.cellSize + thickness));
      return {
        type: "border",
        orientation: "horizontal",
        zone: "game",
        anchor: { row, col },
        direction: "top",
        thickness,
      };
    }

    // vertical borders (between columns)
    for (let col = 1; col < this.board.cols; col++) {
      // variable thickness
      const thickness = offsetX[col] - offsetX[col - 1] - this.board.cellSize;

      // calculate horizontal bounds (skip if outside bounds)
      const left = gameGridStartX.value + offsetX[col] - thickness;
      const right = left + thickness;
      if (x < left || x > right) continue;

      // calculate vertical bounds (skip if outside bounds)
      const top = gameGridStartY.value;
      const bottom = top + offsetY[this.board.rows - 1] - this.board.cellSize;
      if (y < top || y > bottom) continue;

      const row = Math.floor((y - gameGridStartY.value) / (this.board.cellSize + this.board.gap));
      return {
        type: "border",
        orientation: "vertical",
        zone: "game",
        anchor: { row, col },
        direction: "left",
        thickness,
      };
    }

    return null;
  }
}

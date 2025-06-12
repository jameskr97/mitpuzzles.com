import { useGridLayout, useGridPositions } from "@/features/games.components/useGridLayout.ts";
import { useBorderOffsets } from "@/features/games.components/useBorderOffsets.ts";
import { useGutterBorders } from "@/features/games.components/useGutterBorders.ts";
import type { BoardContext } from "@/features/games.components/board.ts";

export type GameZone = "game" | "topGutter" | "bottomGutter" | "leftGutter" | "rightGutter";
type Orientation = "horizontal" | "vertical";

export type Cell = { type: "cell"; row: number; col: number; zone: GameZone };
export type Border = {
  type: "border";
  orientation: Orientation;
  zone: GameZone;
  anchor: { row: number; col: number };
  direction: "top" | "bottom" | "left" | "right";
  thickness: number;
};
export type ClickHit = Cell | Border | { type: "none" };

export interface BoardEvents {
  // Global Events that occur on the website (not associated with a cell)
  // Don't call global ones with dispatchModelEvent. They're assigned in the constructor.
  onMouseDown?(event: MouseEvent): boolean;
  onMouseUp?(event: MouseEvent): boolean;
  onMouseMove?(event: MouseEvent): boolean;
  onKeyDown?(event: KeyboardEvent): boolean;

  // Cell Events
  onCellMouseDown?(cell: Cell, event: MouseEvent): boolean;
  onCellMouseUp?(cell: Cell, event: MouseEvent): boolean;
  onCellClick?(cell: Cell, event: MouseEvent): boolean;
  onCellEnter?(cell: Cell, event: MouseEvent): boolean;
  onCellLeave?(cell: Cell, event: MouseEvent): boolean;
  onCellKeyDown?(cell: Cell, event: KeyboardEvent): boolean;
  onCellInteracted?(cell: Cell, event: MouseEvent): boolean;
  onCellHoveredKeyDown?(cell: Cell, event: KeyboardEvent): boolean;

  // Border Events
  onBorderMouseDown?(border: Border, event: MouseEvent): boolean;
  onBorderMouseUp?(border: Border, event: MouseEvent): boolean;
  onBorderClick?(border: Border, event: MouseEvent): boolean;
  onBorderEnter?(border: Border, event: MouseEvent): boolean;
  onBorderLeave?(border: Border, event: MouseEvent): boolean;

  // Board Events
  onBoardEnter?(event: MouseEvent): boolean;
  onBoardLeave?(event: MouseEvent): boolean;
}

/**
 * Handles user interactions with the game board.
 * NOTE: We emit events to TWO LOCATIONS.
 * 1. The model (PuzzleModelAdapter)
 * 2. The parent component (from the @input-event handler attached to BoardInteraction.vue
 *
 * TODO(james): Some border events are fired, but not all events are fired.
 */
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
  private lastMouseDown: Cell | Border | null = null;
  private lastHover: Cell | null = null;
  private focused: Cell | null = null;
  private isMouseOnBoard: boolean = false; // Track if mouse is on the board

  constructor(
    private board: BoardContext,
    private model: Partial<BoardEvents>,
    private emit?: (event: string, ...payload: any) => void,
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

    // Global Event Listeners
    window.addEventListener("mouseup", (e: MouseEvent) => this.model?.onMouseUp?.(e));
    window.addEventListener("keydown", (e: KeyboardEvent) => {
      if (this.lastHover?.type !== "cell") return; // Only handle keydown if hovering over a cell
      this.model?.onCellHoveredKeyDown?.(this.lastHover, e);
    });
  }

  dispatchModelEvent<K extends keyof BoardEvents>(key: K, hit?: Cell | Border, event?: MouseEvent | KeyboardEvent) {
    this.emit?.(key as string, { hit, event });

    const event_only_funcs = ["onMouseDown", "onMouseUp", "onMouseMove", "onKeyDown"] as const;
    const fn = this.model?.[key];
    if (!fn) return;
    if (event_only_funcs.includes(key as any)) {
      // @ts-expect-error functions correctly, though throws type error
      fn(event);
    } else {
      // @ts-expect-error functions correctly, though throws type error
      fn(hit, event);

      // fire onCellInteracted event
      if (
        hit &&
        hit.type === "cell" &&
        typeof this.model?.onCellInteracted === "function" &&
        key.startsWith("onCell")
      ) {
        this.model?.onCellInteracted(hit as Cell, event as MouseEvent);
      }
    }
  }

  getHit(event: MouseEvent) {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const x = (event.clientX - rect.left) / this.board.scale;
    const y = (event.clientY - rect.top) / this.board.scale;
    const res = this.findCellAt(x, y);

    if (res.type === "none") return null;
    return res;
  }

  // Event Handlers
  /**
   * Mouse Down Event Handler.
   * Called when the user presses the mouse down over a board-element that responds to the click action.
   * @param event The mouse event.
   */
  onMouseDown(event: MouseEvent) {
    const hit = this.getHit(event);
    if (!hit) return;
    this.lastMouseDown = hit;
    this.dispatchModelEvent("onMouseDown", undefined, event);

    switch (hit.type) {
      case "cell":
        this.dispatchModelEvent("onCellMouseDown", hit, event);
        break;
      case "border":
        this.dispatchModelEvent("onBorderMouseDown", hit, event);
        break;
    }
  }

  onMouseUp(event: MouseEvent) {
    const hit = this.getHit(event);
    if (!hit) return;
    this.dispatchModelEvent("onMouseUp", undefined, event);

    switch (hit.type) {
      case "cell": {
        if (
          this.lastMouseDown &&
          this.lastMouseDown.type == "cell" &&
          this.lastMouseDown.row === hit.row &&
          this.lastMouseDown.col === hit.col &&
          this.lastMouseDown.zone === hit.zone
        ) {
          this.dispatchModelEvent("onCellClick", this.lastMouseDown, event);
          this.focused = hit;
        }
        this.dispatchModelEvent("onCellMouseUp", hit, event);
        break;
      }
      case "border":
        if (
          this.lastMouseDown &&
          this.lastMouseDown.type === "border" &&
          this.lastMouseDown.anchor.row === hit.anchor.row &&
          this.lastMouseDown.anchor.col === hit.anchor.col &&
          this.lastMouseDown.zone === hit.zone &&
          this.lastMouseDown.direction === hit.direction
        )
          this.dispatchModelEvent("onBorderClick", hit, event);
        this.dispatchModelEvent("onBorderMouseUp", hit, event);
        break;
    }

    if (hit.type !== "cell") this.focused = null;

    if (hit.type === "cell" && this.lastHover) this.model?.onCellMouseUp?.(hit, event);
  }

  onMouseMove(event: MouseEvent) {
    const hit = this.getHit(event);
    if (!hit) return;
    this.dispatchModelEvent("onMouseMove", undefined, event);

    // Update Focused Cell
    if (hit.type === "cell") {
      // Update Hover Tracking
      if (!this.lastHover || this.lastHover.row !== hit.row || this.lastHover.col !== hit.col) {
        if (this.lastHover) {
          this.dispatchModelEvent("onCellLeave", this.lastHover, event);
        }
        this.dispatchModelEvent("onCellEnter", hit, event);
        this.lastHover = hit;
      }
    } else if (this.lastHover) {
      this.dispatchModelEvent("onCellLeave", this.lastHover, event);
      this.lastHover = null;
    }
  }

  onKeyDown(event: KeyboardEvent) {
    const hit = this.focused;
    if (!hit || hit.type !== "cell") return;
    this.dispatchModelEvent("onKeyDown", hit, event);
    this.dispatchModelEvent("onCellKeyDown", hit, event);
  }

  /**
   * Board Enter Event Handler.
   * Called when the mouse enters the board area.
   * @param event The mouse event.
   */
  onBoardEnter(event: MouseEvent) {
    if (this.isMouseOnBoard) return; // Already on board, skip
    this.isMouseOnBoard = true;
    this.dispatchModelEvent("onBoardEnter", undefined, event);
  }

  /**
   * Board Leave Event Handler.
   * Called when the mouse leaves the board area.
   * @param event The mouse event.
   */
  onBoardLeave(event: MouseEvent) {
    if (!this.isMouseOnBoard) return; // Not on board, skip
    this.isMouseOnBoard = false;
    // Clear last hover cell state when mouse leaves the board
    if (this.lastHover) {
      this.dispatchModelEvent("onCellLeave", this.lastHover, event);
      this.lastHover = null;
    }
    this.dispatchModelEvent("onBoardLeave", undefined, event);
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

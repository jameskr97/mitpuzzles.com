import type { PuzzleModel } from "./PuzzleModelBase.ts";
import type { GameZone } from "@/features/games/components/board.interaction.ts";

export function usePuzzleModelAdapter<T extends PuzzleModel<any>>(model: T) {
  return {
    // CELL EVENTS
    onCellClick: (zone: GameZone, row: number, col: number, event: MouseEvent) => model.onCellClick?.(zone, row, col, event),
    onCellMouseDown: (row: number, col: number, event: MouseEvent) => model.onCellMouseDown?.(row, col, event),
    onCellMouseUp: (row: number, col: number, event: MouseEvent) => model.onCellMouseUp?.(row, col, event),
    onCellRightClick: (zone: GameZone, row: number, col: number, event: MouseEvent) => model.onCellClick?.(zone, row, col, event),
    onCellEnter: (row: number, col: number) => model.onCellMouseEnter?.(row, col),
    onCellLeave: (row: number, col: number) => model.onCellMouseLeave?.(row, col),
    onCellKeyDown: (row: number, col: number, event: KeyboardEvent) => model.onCellKeyDown?.(row, col, event),
    onCellKeyUp: (row: number, col: number, event: KeyboardEvent) => model.onCellKeyUp?.(row, col, event),

    // GUTTER EVENTS
    onClickGutterLeft: (row: number) => model.onRowClick?.(row),
    onClickGutterRight: (row: number) => model.onRowClick?.(row),
    onClickGutterTop: (col: number) => model.onColClick?.(col),
    onClickGutterBottom: (col: number) => model.onColClick?.(col),
  };
}

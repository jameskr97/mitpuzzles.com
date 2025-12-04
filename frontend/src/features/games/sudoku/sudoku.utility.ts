import type { Cell } from "@/core/games/types/puzzle-types.ts";

export function isCellMatch(cell: Cell | null, row: number, col: number, subgridSize: number) {
  if (!cell) return { row: false, col: false, box: false };
  return {
    row: cell.row === row,
    col: cell.col === col,
    box:
      Math.floor(cell.row / subgridSize) === Math.floor(row / subgridSize) &&
      Math.floor(cell.col / subgridSize) === Math.floor(col / subgridSize),
  };
}

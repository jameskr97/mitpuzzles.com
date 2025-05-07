import type { usePuzzleModelAdapter } from "@/features/games/composables/PuzzleModelAdapter.ts";

export type BorderStyle = {
  thickness?: number;
  clickable?: boolean;
  borderClass?: string;
};

export type BoardBordersConfig = {
  rows?: Record<number, BorderStyle>;
  cols?: Record<number, BorderStyle>;
  everyNthRow?: { n: number; style: BorderStyle };
  everyNthCol?: { n: number; style: BorderStyle };
  outer?: BorderStyle;
};

export interface BoardContext {
  rows: number;
  cols: number;
  cellSize: number;
  scale: number;
  gap: number;
  model: ReturnType<typeof usePuzzleModelAdapter>;

  borderConfig: BoardBordersConfig;
  gutters: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
}

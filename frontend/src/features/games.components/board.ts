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
  inner?: BorderStyle;
};

export interface BoardContext {
  rows: number;
  cols: number;
  cellSize: number;
  scale: number;
  gap: number;

  borderConfig: BoardBordersConfig;
  gutters: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
}

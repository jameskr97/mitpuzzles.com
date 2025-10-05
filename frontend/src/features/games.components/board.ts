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
  gutter_visibility?: {
    top_horizontal?: boolean;
    bottom_horizontal?: boolean;
    left_vertical?: boolean;
    right_vertical?: boolean;
  };
  hide_gutter_borders?: boolean | {
    top?: boolean;
    bottom?: boolean;
    left?: boolean;
    right?: boolean;
  };
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

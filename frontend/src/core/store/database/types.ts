export type HistoryMode = "freeplay" | "experiment";

export type GameActionType =
  | "click"
  | "keypress"
  | "hover"
  | "dwell"
  | "clear"
  | "tutorial_toggle"
  | "custom"
  | "puzzle_visible"
  | "puzzle_not_visible"
  | "visibility_summary";

export interface GameEvent {
  id: string;
  puzzle_type: string;
  mode: HistoryMode;
  experiment_id?: string;
  timestamp: number;
  sequence: number;
  action_type: GameActionType;
  cell?: { row: number; col: number };
  key?: string;
  old_value?: number;
  new_value?: number;
  board_snapshot?: number[][];
  custom_data?: Record<string, any>;
}

export interface PuzzleActionPayload {
  action: "click" | "keypress" | "clear" | "focus" | "hover";
  cell: { row: number; col: number };
  old_state?: number;
  new_state?: number;
  timestamp: number;
  before_action?: number[][];
  after_action?: number[][];
  [key: string]: any;
}

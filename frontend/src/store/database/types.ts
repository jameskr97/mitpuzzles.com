export type HistoryMode = "freeplay" | "experiment";


export interface PuzzleActionPayload {
  action: "click" | "keypress" | "clear" | "focus" | "hover";
  cell: { row: number; col: number };
  old_state?: number;
  new_state?: number;
  timestamp: number;
  before_action?: number[][];
  after_action?: number[][];
  [key: string]: any; // Allow additional properties
}

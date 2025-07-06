export type HistoryMode = 'freeplay' | 'experiment';

export interface PuzzleMetadata {
  id: string;
  variants: string[][];
  selected_variant: string[];
  cacheVersion: number;
}

export interface PuzzleAttemptData {
  id: string;
  solving_time: number;
  solved: boolean;
  completion_duration_ms: number | null;
  completed_at: number | null;
}

export interface PuzzleActionHistory {
  id: string;
  puzzle_type: string;
  mode: HistoryMode;
  event_order: number;
  event_payload: any;
  created_at: number;
}

export interface PuzzleActionPayload {
  action: "click" | "keypress" | "clear";
  cell: { row: number; col: number };
  old_state?: number;
  new_state?: number;
  timestamp: number;
  before_action?: number[][];
  after_action?: number[][];
}

export interface PuzzleStateData {
  id: string;
  state: number[][];
  lastUpdated: number;
}

export interface PuzzleScale {
  id: string;
  scale: number;
}

export interface CacheInfo {
  id: string;
  currentVersion: number;
}

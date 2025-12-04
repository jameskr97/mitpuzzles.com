/**
 * useDataRecorder - Mode-agnostic data recording
 *
 * Supports both:
 * - Freeplay: Persistence to IndexedDB, cross-tab broadcast
 * - Experiment: Recording to GraphExecutor data collection
 */
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore.ts";
import { broadcast_channel_service } from "@/core/services/broadcast_channel.ts";
import type { Cell } from "@/core/games/types/puzzle-types.ts";

export interface DataRecorderConfig {
  /**
   * Recording mode
   */
  mode: "freeplay" | "experiment";

  /**
   * Puzzle type identifier
   */
  puzzle_type: string;

  /**
   * Freeplay: Enable persistence to IndexedDB
   */
  persist?: boolean;

  /**
   * Freeplay: Enable cross-tab broadcast
   */
  broadcast?: boolean;

  /**
   * Experiment: GraphExecutor for data collection
   */
  executor?: any; // GraphExecutor type

  /**
   * Experiment: Current trial ID
   */
  trial_id?: string;

  /**
   * Experiment: Current node ID
   */
  node_id?: string;
}

export interface DataRecorderReturn {
  /**
   * Record a cell click interaction
   */
  record_click: (
    cell: Cell,
    old_value: number,
    new_value: number,
    board?: number[][]
  ) => void;

  /**
   * Record a keypress interaction
   */
  record_keypress: (
    key: string,
    cell: Cell,
    old_value: number,
    new_value: number,
    board?: number[][]
  ) => void;

  /**
   * Record cell focus (hover/selection)
   */
  record_focus: (cell: Cell) => void;

  /**
   * Record board clear action
   */
  record_clear: (old_board: number[][], new_board: number[][]) => void;

  /**
   * Record solution attempt
   */
  record_attempt_solve: (correct: boolean) => void;

  /**
   * Save board state (freeplay only)
   */
  save_board_state: (board: number[][]) => Promise<void>;
}

/**
 * Create a data recorder for game interactions
 */
export function useDataRecorder(config: DataRecorderConfig): DataRecorderReturn {
  const {
    mode,
    puzzle_type,
    persist = true,
    broadcast = true,
    executor,
    trial_id,
    node_id,
  } = config;

  // Freeplay stores (only initialized if needed)
  let progress_store: ReturnType<typeof usePuzzleProgressStore> | null = null;
  let history_store: ReturnType<typeof usePuzzleHistoryStore> | null = null;

  if (mode === "freeplay") {
    progress_store = usePuzzleProgressStore();
    history_store = usePuzzleHistoryStore();
  }

  /**
   * Record to experiment data collection
   */
  function record_to_experiment(
    interaction_type: string,
    data: Record<string, any>
  ): void {
    if (!executor?.data_collection) {
      console.warn("useDataRecorder: no executor data_collection available");
      return;
    }

    executor.data_collection.record_interaction(
      interaction_type,
      node_id ?? "unknown-node",
      {
        ...data,
        timestamp: Date.now(),
      },
      trial_id ?? executor.current_trial_id
    );
  }

  /**
   * Record to freeplay history
   */
  function record_to_freeplay(
    action_type: string,
    data: Record<string, any>
  ): void {
    if (!history_store) return;

    history_store.add_event(puzzle_type, "freeplay", action_type, data);
  }

  /**
   * Record a cell click interaction
   */
  function record_click(
    cell: Cell,
    old_value: number,
    new_value: number,
    board?: number[][]
  ): void {
    const data = {
      cell: { row: cell.row, col: cell.col },
      old_value,
      new_value,
      ...(board && { old_board: board, new_board: board }),
    };

    if (mode === "experiment") {
      record_to_experiment("cell_click", data);
    } else {
      record_to_freeplay("cell_click", data);
    }
  }

  /**
   * Record a keypress interaction
   */
  function record_keypress(
    key: string,
    cell: Cell,
    old_value: number,
    new_value: number,
    board?: number[][]
  ): void {
    const data = {
      key,
      cell: { row: cell.row, col: cell.col },
      old_value,
      new_value,
      ...(board && { old_board: board, new_board: board }),
    };

    if (mode === "experiment") {
      record_to_experiment("cell_keypress", data);
    } else {
      record_to_freeplay("cell_keypress", data);
    }
  }

  /**
   * Record cell focus
   */
  function record_focus(cell: Cell): void {
    const data = {
      cell: { row: cell.row, col: cell.col },
    };

    if (mode === "experiment") {
      record_to_experiment("cell_focus", data);
    }
    // Freeplay doesn't track focus events currently
  }

  /**
   * Record board clear action
   */
  function record_clear(old_board: number[][], new_board: number[][]): void {
    const data = {
      old_board,
      new_board,
    };

    if (mode === "experiment") {
      record_to_experiment("clear", data);
    } else {
      record_to_freeplay("clear", data);
    }
  }

  /**
   * Record solution attempt
   */
  function record_attempt_solve(correct: boolean): void {
    const data = { correct };

    if (mode === "experiment") {
      record_to_experiment("attempt_solve", data);
    } else {
      record_to_freeplay("attempt_solve", data);
    }
  }

  /**
   * Save board state (freeplay only)
   */
  async function save_board_state(board: number[][]): Promise<void> {
    if (mode !== "freeplay" || !progress_store) return;

    if (persist) {
      await progress_store.update_puzzle_state(puzzle_type, board);
    }

    if (broadcast) {
      broadcast_channel_service.broadcast_state_update(puzzle_type, board);
    }
  }

  return {
    record_click,
    record_keypress,
    record_focus,
    record_clear,
    record_attempt_solve,
    save_board_state,
  };
}

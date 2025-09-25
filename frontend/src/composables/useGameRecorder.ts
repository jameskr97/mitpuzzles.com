/**
 * game recorder composable - records user actions
 **/
import { computed, inject,  ref } from "vue";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { usePuzzleHistoryStore } from "@/store/puzzle/usePuzzleHistoryStore.ts";
import type { ExperimentContext } from "@/features/experiment/composables/useExperimentContext.ts";

export interface GameRecorderOptions {
  enabled?: boolean;
  mode?: "freeplay" | "experiment";
  capture_board_snapshots?: boolean;
  capture_hover_events?: boolean;
  hover_threshold_ms?: number;
}

/**
 * game recorder behavior - tracks all user interactions for research
 */
export function useGameRecorder(options: GameRecorderOptions = {}) {
  const {
    enabled: initialEnabled = true,
    mode: initialMode = "freeplay",
    capture_board_snapshots = true,
    capture_hover_events = false,
    hover_threshold_ms = 500,
  } = options;

  // configuration
  const enabled = ref(initialEnabled);
  const mode = ref(initialMode);
  const capture_snapshots = ref(capture_board_snapshots);
  const capture_hovers = ref(capture_hover_events);
  const hover_threshold = ref(hover_threshold_ms);

  // dependencies
  const historyStore = usePuzzleHistoryStore();
  const experimentContext = inject<ExperimentContext>("experiment");

  // hover tracking state
  const current_hover_cell = ref<Cell | null>(null);
  const hover_start_time = ref<number | null>(null);


  // helper functions
  const set_mode = (newMode: "freeplay" | "experiment") => {
    mode.value = newMode;
  }


  const shouldRecord = computed(() => {
    if (!enabled.value) return false;

    if (mode.value === "experiment") {
      return experimentContext && experimentContext.definition && experimentContext.currentTrial.value;
    }

    return mode.value === "freeplay";
  });

  const getCustomData = () => {
    if (!(mode.value === "experiment" && experimentContext)) return {}; // freeplay mode or no context
    return {
      experiment_id: experimentContext.definition?.id,
      stage_id: experimentContext.currentTrial.value?.id.toString(),
      trial_id: experimentContext.currentTrial.value?.id.toString(),
    };
  };

  // recording methods - now take puzzle_type as parameter
  const record_click = async (puzzle_type: string, cell: Cell, old_value?: number, new_value?: number, board_snapshot?: number[][]) => {
    if (!shouldRecord.value) return;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "click",
      {
        cell: { row: cell.row, col: cell.col },
        old_value,
        new_value,
        board_snapshot: capture_snapshots.value ? board_snapshot : undefined,
        custom_data: getCustomData(),
      }
    );
  };

  const record_keypress = async (puzzle_type: string, key: string, cell: Cell, old_value?: number, new_value?: number, board_snapshot?: number[][]) => {
    if (!shouldRecord.value) return;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "keypress",
      {
        cell: { row: cell.row, col: cell.col },
        old_value,
        new_value,
        board_snapshot: capture_snapshots.value ? board_snapshot : undefined,
        custom_data: getCustomData(),
      }
    );
  };

  const record_hover = async (puzzle_type: string, cell: Cell, duration: number) => {
    if (!shouldRecord.value || !capture_hovers.value) return;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "hover",
      {
        cell: { row: cell.row, col: cell.col },
        custom_data: {
          ...getCustomData(),
          hover_duration_ms: duration,
          hover_threshold_ms: hover_threshold.value,
        },
      }
    );
  };

  const record_dwell = async (puzzle_type: string, cell: Cell, enter_time: number, leave_time: number) => {
    if (!shouldRecord.value || !capture_hovers.value) return;

    const dwell_duration = leave_time - enter_time;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "dwell",
      {
        cell: { row: cell.row, col: cell.col, zone: cell.zone },
        custom_data: {
          ...getCustomData(),
          enter_time,
          leave_time,
          dwell_duration,
          threshold_ms: hover_threshold.value,
        },
      }
    );
  };

  const record_tutorial_toggle = async (puzzle_type: string, tutorial_enabled: boolean) => {
    if (!shouldRecord.value) return;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "tutorial_toggle",
      {
        custom_data: {
          ...getCustomData(),
          tutorial_enabled,
        },
      }
    );
  };

  const record_clear = async (puzzle_type: string, board_before?: number[][], board_after?: number[][]) => {
    if (!shouldRecord.value) return;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "clear",
      {
        custom_data: {
          ...getCustomData(),
          board_before,
          board_after,
        },
      }
    );
  };

  const record_custom_event = async (puzzle_type: string, event_name: string, data: any) => {
    if (!shouldRecord.value) return;

    await historyStore.add_event(
      puzzle_type,
      mode.value,
      "custom",
      {
        custom_data: {
          ...getCustomData(),
          event_name,
          ...data,
        },
      }
    );
  };

  // hover timer management
  const startHoverTimer = (puzzle_type: string, cell: Cell) => {
    if (!capture_hovers.value) return;

    clearHoverTimer();
    current_hover_cell.value = cell;
    hover_start_time.value = Date.now();
  };

  const endHoverTimer = (puzzle_type: string) => {
    if (hover_start_time.value && current_hover_cell.value) {
      const duration = Date.now() - hover_start_time.value;

      // record hover event regardless of duration
      record_hover(puzzle_type, current_hover_cell.value, duration);

      // record dwell event only if duration >= threshold
      if (duration >= hover_threshold.value)
        record_dwell(puzzle_type, current_hover_cell.value, hover_start_time.value, Date.now());
    }
    clearHoverTimer();
    hover_start_time.value = null;
  };

  const clearHoverTimer = () => {
    current_hover_cell.value = null;
  };


  // cleanup function
  const cleanup = () => {
    clearHoverTimer();
    hover_start_time.value = null;
  };

  // export actions for a specific experiment
  const export_experiment_actions = async (experiment_id: string) => {
    await historyStore.init(); // ensure store is initialized
    const events = historyStore.get_events(experiment_id, "experiment");

    // Group events by trial (using custom_data.trial_id or stage_id)
    const groupedByTrial: Record<string, any[]> = {};

    events.forEach(event => {
      const trialId = event.custom_data?.trial_id || event.custom_data?.stage_id || "unknown";
      if (!groupedByTrial[trialId]) {
        groupedByTrial[trialId] = [];
      }

      // Format action data for export (similar to freeplay format)
      const formattedAction = {
        action: event.action_type,
        timestamp: event.timestamp,
        sequence: event.sequence,
        cell: event.cell,
        key: event.key,
        old_value: event.old_value,
        new_value: event.new_value,
        old_board: event.custom_data?.old_board,
        new_board: event.custom_data?.new_board,
        custom_data: event.custom_data,
      };

      groupedByTrial[trialId].push(formattedAction);
    });

    // Sort events within each trial by sequence
    Object.keys(groupedByTrial).forEach(trialId => {
      groupedByTrial[trialId].sort((a, b) => a.sequence - b.sequence);
    });

    return groupedByTrial;
  };

  return {
    // configuration
    set_mode,

    // recording methods - now take puzzle_type as first parameter
    record_click,
    record_keypress,
    record_hover,
    record_dwell,
    record_clear,
    record_tutorial_toggle,
    record_custom_event,


    // export functionality
    export_experiment_actions,

    // state access
    state: {
      enabled: computed(() => enabled.value),
      mode: computed(() => mode.value),
      capture_snapshots: computed(() => capture_snapshots.value),
      capture_hovers: computed(() => capture_hovers.value),
      hover_threshold: computed(() => hover_threshold.value),
      should_record: shouldRecord,
      current_hover_cell: computed(() => current_hover_cell.value),
    },

    // utility methods
    cleanup,
    clearHoverTimer,
    startHoverTimer,
    endHoverTimer,
  };
}

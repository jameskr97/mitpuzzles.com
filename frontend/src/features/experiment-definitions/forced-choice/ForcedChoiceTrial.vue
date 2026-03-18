<script setup lang="ts">
import { computed, inject, onMounted, ref, type Ref, toRef } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { Button } from "@/core/components/ui/button";
import { useStateMachine } from "@/features/experiment-core/composables/useStateMachine.ts";
import { createLogger } from "@/core/services/logger.ts";
const log = createLogger("experiment:forced_choice");
import { useTimer } from "@/features/experiment-core/composables/useTimer.ts";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import PuzzleSelector from "./PuzzleSelector.vue";
import { useExperimentPuzzle } from "@/features/experiment-core/composables/useExperimentPuzzle.ts";
import { remap } from "@/core/services/util.ts";
import { GraphExecutor } from "@/features/experiment-core";
import { shuffle } from "@/utils";
import MinesweeperCanvas from "@/features/games/minesweeper/MinesweeperCanvas.vue";

// props from experiment-core trial system
const props = defineProps<{
  stimulus_item: PuzzleDefinition[]; // puzzle pair data
  trial_index: number;
}>();

const emit = defineEmits<{
  "trial-complete": [result: any];
}>();

enum trial_state {
  preview = "preview",
  choice = "choice",
  solving = "solving",
  complete = "complete",
}

interface trial_data {
  puzzle_id: string;
  selected_puzzle_index: number;
  display_order: number[]; // [0, 1] means normal order, [1, 0] means swapped
  choice_phase_data: {
    preview_duration: number;
    total_choice_time: number;
    puzzle_selection_log: Array<{ selected_puzzle_id: string; timestamp: number; selected_duration: number }>;
    was_auto_selected: boolean;
  };
  solving_phase_data: {
    solving_time: number;
    completed: boolean;
    final_board_state: any;
  };
  timestamps: {
    preview_start: number;
    preview_end: number;
    choice_start: number;
    choice_end: number;
    solving_start: number;
    solving_end: number;
  };
}

// puzzle controller for solving phase - use reactive ref for puzzle definition
const executor = inject<Ref<GraphExecutor>>("experiment-executor");
const current_puzzle_for_solving = ref<PuzzleDefinition>(props.stimulus_item[0]);
const pc = ref(useExperimentPuzzle(current_puzzle_for_solving, executor!));

// randomize puzzle display order once per trial
const shuffled_puzzles = shuffle([...props.stimulus_item]);

// state management
const selected_puzzle_index = ref<number | null>(null);
const current_viewing_puzzle_index = ref<number | null>(null);
const has_viewed_any_puzzle = ref(false);
const game_scale = ref(50);

// timers
const preview_timer = useTimer({ duration_seconds: 2 });
const choice_timer = useTimer({ duration_seconds: 30 });
const solving_timer = useTimer({ duration_seconds: 60 });

// data collection
const trial_result = ref<Partial<trial_data>>({
  display_order: shuffled_puzzles.map((puzzle) => props.stimulus_item.findIndex((p) => p.id === puzzle.id)),
  choice_phase_data: {
    preview_duration: 0,
    total_choice_time: 0,
    puzzle_selection_log: [],
    was_auto_selected: false,
  },
  solving_phase_data: {
    solving_time: 0,
    completed: false,
    final_board_state: null,
  },
  timestamps: {} as any,
});

const game_scale_remapped = computed(() => remap([1, 100], [1, 4], game_scale.value));

// state machine
const state_machine = useStateMachine<trial_state>({
  state_initial: trial_state.preview,
  states: {
    [trial_state.preview]: {
      canTransitionTo: [trial_state.choice],
      onEnter: () => {
        log("entered preview phase");

        trial_result.value.timestamps!.preview_start = Date.now();
        preview_timer.start(() => {
          state_machine.transitionTo(trial_state.choice);
        });
      },
      onExit: () => {
        preview_timer.stop();
        trial_result.value.timestamps!.preview_end = Date.now();
        trial_result.value.choice_phase_data!.preview_duration =
          trial_result.value.timestamps!.preview_end - trial_result.value.timestamps!.preview_start;
      },
    },
    [trial_state.choice]: {
      canTransitionTo: [trial_state.solving],
      canTransition: () => selected_puzzle_index.value !== null,
      onEnter: () => {
        log("entered choice phase");
        trial_result.value.timestamps!.choice_start = Date.now();
      },
      onExit: () => {
        choice_timer.stop()
        // update last selection log entry duration
        const log = trial_result.value.choice_phase_data!.puzzle_selection_log;
        if (log.length > 0) {
          const final_entry = log[log.length - 1];
          final_entry.selected_duration = Date.now() - final_entry.timestamp;
        }

        trial_result.value.timestamps!.choice_end = Date.now();
        trial_result.value.choice_phase_data!.total_choice_time = trial_result.value.timestamps!.choice_end - trial_result.value.timestamps!.choice_start;
        trial_result.value.selected_puzzle_index = selected_puzzle_index.value!;

        // update puzzle controller with selected puzzle for solving phase
        update_puzzle_for_solving();
      },
    },
    [trial_state.solving]: {
      canTransitionTo: [trial_state.complete],
      onEnter: () => {
        log("entered solving phase");
        trial_result.value.timestamps!.solving_start = Date.now();
        solving_timer.start(() => {
          trial_result.value.solving_phase_data!.completed = false;
          state_machine.transitionTo(trial_state.complete);
        });
      },
      onExit: () => {
        solving_timer.stop();
        trial_result.value.timestamps!.solving_end = Date.now();
        trial_result.value.solving_phase_data!.solving_time =
          trial_result.value.timestamps!.solving_end - trial_result.value.timestamps!.solving_start;
        trial_result.value.solving_phase_data!.final_board_state = pc.value.state_puzzle.board;
      },
    },
    [trial_state.complete]: {
      onEnter: () => {
        log("trial complete - saving data");

        // record trial completion using experiment store
        if (executor?.value?.data_collection && pc.value) {
          const correct_cells = pc.value.get_correct_cells?.() || [];
          const incorrect_cells = pc.value.get_incorrect_cells?.() || [];
          const is_correct = correct_cells.length !== 0 && incorrect_cells.length === 0;

          executor.value.data_collection.record_trial_end(
            pc.value.state_puzzle.definition.id,
            is_correct,
            undefined,
            {
              final_board: pc.value.state_puzzle.board,
              correct_cells_count: correct_cells.length,
              incorrect_cells_count: incorrect_cells.length,
              choice_phase: trial_result.value.choice_phase_data,
              solving_phase: trial_result.value.solving_phase_data,
              timestamps: trial_result.value.timestamps,
            },
          );
        }
      },
    },
  },
});

// helper function to start choice timer
function start_choice_timer() {
  choice_timer.start(() => {
    // auto-select last viewed puzzle or default to first puzzle (original index)
    if (selected_puzzle_index.value === null) {
      const fallback_shuffled_index = current_viewing_puzzle_index.value ?? 0;
      const fallback_puzzle = shuffled_puzzles[fallback_shuffled_index];
      selected_puzzle_index.value = props.stimulus_item.findIndex((p) => p.id === fallback_puzzle.id);
      trial_result.value.choice_phase_data!.was_auto_selected = true;
    }
    state_machine.transitionTo(trial_state.solving);
  });
}

// update puzzle controller with selected puzzle data for solving phase
function update_puzzle_for_solving() {
  const selected_puzzle = props.stimulus_item[selected_puzzle_index.value!];
  if (!selected_puzzle) throw Error("Selected Puzzle is undefined - can't create puzzle controller");

  // update the reactive puzzle definition - this will trigger the engine to recreate
  current_puzzle_for_solving.value = selected_puzzle;
  pc.value = useExperimentPuzzle(toRef(selected_puzzle), executor!);
}

function p2_select_puzzle(shuffled_index: number) {
  if (shuffled_index < 0 || shuffled_index >= shuffled_puzzles.length) {
    console.error("invalid puzzle index selected:", shuffled_index);
    return;
  }

  // find original index for the selected puzzle
  const selected_puzzle = shuffled_puzzles[shuffled_index];
  const original_index = props.stimulus_item.findIndex((p) => p.id === selected_puzzle.id);

  selected_puzzle_index.value = original_index;

  const log = trial_result.value.choice_phase_data!.puzzle_selection_log;
  if (log.length > 0) {
    const previous_entry = log[log.length - 1];
    previous_entry.selected_duration = Date.now() - previous_entry.timestamp;
  }

  // start choice timer on first puzzle view
  if (!has_viewed_any_puzzle.value) {
    has_viewed_any_puzzle.value = true;
    start_choice_timer();
  }

  // track puzzle view using original puzzle id
  trial_result.value.choice_phase_data!.puzzle_selection_log.push({
    selected_puzzle_id: selected_puzzle.id,
    timestamp: Date.now(),
    selected_duration: 0, // will be updated when switching away
  });
}

// computed properties
const can_proceed_to_solving = computed(() => selected_puzzle_index.value !== null);

async function handle_submit() {
  log("handle_submit called");
  const result = await pc.value.check_solution();
  log("check_solution result: %O", result);
  if (result) {
    trial_result.value.solving_phase_data!.completed = true;
    state_machine.transitionTo(trial_state.complete);
  }
}

onMounted(() => {
  state_machine.reset();
  if (executor?.value?.data_collection) {
    executor.value.data_collection.record_trial_start(props.trial_index, props.stimulus_item);
  }
});
</script>

<template>
  <div class="mx-auto w-full pb-2 max-w-prose">
    <!-- phase 1 - preview: show both puzzles for initial preview time -->
    <div v-if="state_machine.current_state.value === trial_state.preview" class="flex flex-col gap-5">
      <Container class="text-center">
        <div class="text-xl mb-4">Puzzle Preview</div>
        <div class="text-lg italic">{{ preview_timer.time_remaining.value }}s remaining</div>
      </Container>
      <PuzzleSelector :puzzles="shuffled_puzzles" :force-visible="true" :enable-interaction="false" />
    </div>

    <!-- phase 2 - choice: navigate and select puzzle -->
    <div v-else-if="state_machine.current_state.value === trial_state.choice" class="flex flex-col gap-2">
      <Container class="text-center">
        <div class="text-xl mb-2">Use arrow keys or click to toggle between puzzles</div>
        <div class="text-sm italic"></div>
        <div class="text-lg font-mono">{{ choice_timer.time_remaining.value }}s remaining</div>
      </Container>

      <PuzzleSelector
        class="h-55"
        :puzzles="shuffled_puzzles"
        @selection-changed="(_from_index, to_index) => p2_select_puzzle(to_index)"
      />

      <!-- proceed button -->
      <div class="text-center">
        <Button
          variant="default"
          :disabled="!can_proceed_to_solving"
          @click="() => state_machine.transitionTo(trial_state.solving)"
        >
          Solve Selected Puzzle
        </Button>
      </div>
    </div>

    <!-- phase 3 - solving -->
    <div v-else-if="state_machine.current_state.value === trial_state.solving" class="flex flex-col gap-5">
      <Container class="text-center">
        <div class="text-xl mb-2">Solve the puzzle</div>
        <div class="text-lg font-mono">{{ solving_timer.time_remaining.value }}s remaining</div>
      </Container>

      <!-- scale control -->
      <div class="flex flex-row w-full">
        <v-icon name="co-magnifying-glass" :scale="1.5" />
        <input v-model="game_scale" type="range" min="1" max="100" step="1" class="mx-2 w-full" />
      </div>

      <!-- Minesweeper Canvas -->
      <div class="flex flex-col items-center">
          <div :class="{ 'shake-once': pc.state_ui.animate_failure, 'heartbeat-once': pc.state_ui.animate_success }">
            <Container v-if="pc" :style="{ width: `${pc.state_puzzle.definition.cols * 32 * game_scale_remapped}px`, height: `${pc.state_puzzle.definition.rows * 32 * game_scale_remapped}px` }">
              <MinesweeperCanvas
                :state="pc.state_puzzle"
                @cell-click="(row, col, button) => pc.handle_cell_click({ row, col }, { button } as MouseEvent)"
              />
            </Container>
            <div v-else class="p-4 text-red-500">puzzle state not properly initialized</div>
        </div>
      </div>

      <!-- Continue Button -->
      <div class="text-center">
        <Button variant="default" @click="handle_submit">
          Submit
        </Button>
      </div>
    </div>

    <!-- phase 4 - intermission -->
    <div v-else-if="state_machine.current_state.value === trial_state.complete" class="flex flex-col gap-5">
      <div class="text-3xl text-center mt-2">Trial Complete!</div>
      <div v-if="pc" class="flex justify-center">
        <div :style="{ width: `${pc.state_puzzle.definition.cols * 32 * game_scale_remapped}px`, height: `${pc.state_puzzle.definition.rows * 32 * game_scale_remapped}px` }">
          <MinesweeperCanvas :state="pc.state_puzzle" />
        </div>
      </div>
      <Button
        variant="default"
        @click="$emit('trial-complete', trial_result)"
        class="bg-green-600 hover:bg-green-700 w-full"
      >
        Next Trial
      </Button>
    </div>

    <!-- phase error: this shouldn't happen -->
    <div v-else class="text-center text-red-500">unknown state: {{ state_machine.current_state.value }}</div>
  </div>
</template>

<style scoped></style>

<script setup lang="ts">
import { computed, inject, onMounted, type Ref, ref, toRef } from "vue";
import { Button } from "@/core/components/ui/button";
import Container from "@/core/components/ui/Container.vue";
import { useExperimentPuzzle } from "@/features/experiment-core/composables/useExperimentPuzzle";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import type { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import SudokuCanvas from "@/features/games/sudoku/SudokuCanvas.vue";

const props = defineProps<{
  stimulus_item: PuzzleDefinition[];
  trial_index: number;
}>();

const emit = defineEmits(["trial-complete"]);

// inject executor for points management
const executor = inject<Ref<GraphExecutor>>("experiment-executor")!;

// Ensure the puzzle is as it should be
if (props.stimulus_item.length !== 1)
  throw new Error("BlindSudokuTrial cannot support more than one trial per puzzle.");

// Trial phases
const phase = ref<"playing" | "feedback">("playing");
// Performance tracking
const correct_cells = ref<number>(0);
const incorrect_cells = ref<number>(0);
const points = ref<number>(0);

// check if all fillable cells are completed
const all_cells_filled = computed(() => {
  const board = pc.state_puzzle.value.board;
  const initial_state = pc.state_puzzle.value.definition.initial_state;

  for (let row = 0; row < board.length; row++) {
    for (let col = 0; col < board[row].length; col++) {
      // if this cell was initially empty (-1) and is still empty (-1), puzzle is incomplete
      if (initial_state[row][col] === -1 && board[row][col] === -1) {
        return false;
      }
    }
  }
  return true;
});

// Finish trial - calculate performance and show feedback
function finish_trial() {
  const incorrect = pc.get_incorrect_cells?.() || [];
  const correct = pc.get_correct_cells?.() || [];

  // set validation state for canvas rendering
  correct_cells_list.value = correct;
  incorrect_cells_list.value = incorrect;

  correct_cells.value = correct.length;
  incorrect_cells.value = incorrect.length;

  // Calculate points (same logic as original blind-sudoku)
  const POINTS_MULTIPLIER = 2;
  points.value = correct.length * POINTS_MULTIPLIER;
  points.value = Math.max(0, points.value);

  // record trial completion using experiment store
  executor.value.data_collection.record_trial_end(
    null,
    correct.length > 0, // success if any cells correct
    points.value,
    {
      final_board: pc.state_puzzle.value.board,
      correct_cells_count: correct.length,
      incorrect_cells_count: incorrect.length,
      points_multiplier: POINTS_MULTIPLIER,
    },
  );

  // also record points in experiment store for display
  executor?.value.data_collection.add_points(points.value, "trial_completion", props.trial_index);
  phase.value = "feedback";
}

// get puzzle definition
const puzzle = computed(
  (): PuzzleDefinition => (Array.isArray(props.stimulus_item) ? props.stimulus_item[0] : props.stimulus_item),
);

// use new experiment-aware puzzle controller
const pc = useExperimentPuzzle(toRef(puzzle), executor);

// validation state for feedback phase
const correct_cells_list = ref<Array<{ row: number; col: number }>>([]);
const incorrect_cells_list = ref<Array<{ row: number; col: number }>>([]);

function handle_cell_key(row: number, col: number, key: string) {
  if (phase.value !== "playing") return;
  pc.handle_cell_key_down({ row, col }, { key } as KeyboardEvent);
}

onMounted(() => {
  executor!.value.data_collection.record_trial_start(props.trial_index, props.stimulus_item);
});
</script>

<template>
  <div class="blind-sudoku-trial">
    <div v-if="phase === 'playing'" class="trial-content">
      <div class="mb-4 mt-2">
        <div v-if="puzzle" class="puzzle-container flex justify-center">
          <SudokuCanvas
            class="max-w-100"
            :state="pc.state_puzzle.value"
            :blur_mode="true"
            :hover_highlight="true"
            @cell-key="handle_cell_key"
          />
        </div>
        <div v-else class="text-center text-gray-500">
          <p>puzzle component not found for type: {{ pc.state_puzzle.value.definition.puzzle_type }}</p>
        </div>
      </div>

      <Button variant="blue" @click="finish_trial" :disabled="!all_cells_filled" class="w-full">
        Check Answers
      </Button>
    </div>

    <!-- Feedback Phase -->
    <div v-else-if="phase === 'feedback'" class="feedback-content mt-2">
      <Container class="mb-4 text-center">
        <h3 class="text-xl font-bold mb-4">Trial Complete!</h3>

        <div class="stats grid grid-cols-3 gap-4 mb-4">
          <div class="stat-item">
            <div class="text-2xl font-bold text-green-600">{{ correct_cells }}</div>
            <div class="text-sm text-gray-600">Correct</div>
          </div>
          <div class="stat-item">
            <div class="text-2xl font-bold text-red-600">{{ incorrect_cells }}</div>
            <div class="text-sm text-gray-600">Incorrect</div>
          </div>
          <div class="stat-item">
            <div class="text-2xl font-bold text-blue-600">{{ points }}</div>
            <div class="text-sm text-gray-600">Points</div>
          </div>
        </div>

        <div v-if="puzzle" class="puzzle-feedback flex justify-center mb-4">
          <SudokuCanvas
            class="max-w-100"
            :state="pc.state_puzzle.value"
            :correct_cells="correct_cells_list"
            :incorrect_cells="incorrect_cells_list"
            :interactive="false"
          />
        </div>
      </Container>

      <Button variant="green" @click="$emit('trial-complete')" class="w-full">
        Next Trial
      </Button>
    </div>
  </div>
</template>

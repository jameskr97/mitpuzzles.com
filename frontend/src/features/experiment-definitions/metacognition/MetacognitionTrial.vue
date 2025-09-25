<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, type Ref, ref, watch } from "vue";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container.vue";
import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from "@/components/ui/number-field";
import { useExperimentPuzzle } from "@/features/experiment-core/composables/useExperimentPuzzle";
import type { PuzzleDefinition } from "@/services/game/engines/types";
import type { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import PuzzleRenderer from "@/components/PuzzleRenderer.vue";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import { MinesweeperCell, PuzzleConverter } from "@/services/game/engines/translator";
import ExperimentInputSlider from "@/features/experiment-core/components/input/ExperimentInputSlider.vue";
import { useStateMachine } from "@/features/experiment-core/composables/useStateMachine.ts";
import { useTimer } from "@/features/experiment-core/composables/useTimer.ts";

// props and emits
const props = defineProps<{ stimulus_item: PuzzleDefinition[]; trial_index: number }>();
const emit = defineEmits(["trial-complete"]);
const executor = inject<Ref<GraphExecutor>>("experiment-executor")!;

// validation checking
if (props.stimulus_item.length !== 1)
  throw new Error("metacognition trial cannot support more than one puzzle per trial");

// trial states
enum trial_state {
  preview = "preview",
  prospective = "prospective",
  solving = "solving",
  retrospective = "retrospective",
  complete = "complete",
}

// trial state and timers
const puzzle = computed((): PuzzleDefinition => props.stimulus_item[0]);
const pc = useExperimentPuzzle(ref(puzzle), executor);
const bridge = createPuzzleInteractionBridge(pc);

const preview_timer = useTimer({ duration_seconds: 5 });
const solving_timer = useTimer({ duration_seconds: 30 });

// trial configuration
const trial_config = computed(() => {
  const current_node = executor?.value.current_node;
  if (!current_node?.config.meta) throw new Error("no trial config found");

  return {
    preview_times: current_node.config.meta.preview_times || [5],
    prediction_times: current_node.config.meta.prediction_times || [5, 10, 30],
    time_limits: current_node.config.meta.time_limits || [5, 10, 30],
  };
});

// trial data
const selected_preview_time = ref(0);
const selected_time_limit = ref(0);
const prospective_responses = ref({ estimates: {} as Record<number, number>, confidence: 50 });
const retrospective_responses = ref({ estimate: null as number | null, confidence: 50 });

// trial timestamps for data collection
const trial_timestamps = ref({
  preview_start: 0,
  preview_end: 0,
  prospective_start: 0,
  prospective_end: 0,
  solving_start: 0,
  solving_end: 0,
  retrospective_start: 0,
  retrospective_end: 0,
});

// computed puzzle metrics
const number_of_initial_unmarked_cells = PuzzleConverter.fromResearch(
  puzzle.value.initial_state,
  puzzle.value.puzzle_type,
)
  .flat()
  .filter((c) => c === MinesweeperCell.UNMARKED).length;

const currently_marked_cells = computed(() => {
  return pc.state_puzzle.value.board
    .flat()
    .filter((cell) => cell === MinesweeperCell.FLAG || cell === MinesweeperCell.SAFE).length;
});

// validation
const current_correctly_marked_cells = computed(() => {
  if (!puzzle.value.solution) return 0;
  const solution = PuzzleConverter.fromResearch(puzzle.value.solution, puzzle.value.puzzle_type);
  const user_board = pc.state_puzzle.value.board;
  const matching = [MinesweeperCell.FLAG, MinesweeperCell.SAFE];

  let count = 0;
  for (let i = 0; i < solution.length; i++) {
    for (let j = 0; j < solution[i].length; j++) {
      if (!matching.includes(user_board[i][j])) continue;
      if (user_board[i][j] !== solution[i][j]) continue;
      count++;
    }
  }
  return count;
});
const can_proceed_from_retrospective = computed(() =>
  retrospective_responses.value.estimate !== null && retrospective_responses.value.confidence !== 50
);
const can_proceed_from_prospective = computed(() => {
  const required_estimates = trial_config.value.prediction_times.every(
    (time: number) => prospective_responses.value.estimates[time] != null,
  );
  const has_confidence = prospective_responses.value.confidence !== 50;
  return required_estimates && has_confidence;
});

// state machine
const state_machine = useStateMachine<trial_state>({
  state_initial: trial_state.preview,
  states: {
    [trial_state.preview]: {
      canTransitionTo: [trial_state.prospective],
      onEnter: () => {
        console.log("entered preview phase");
        trial_timestamps.value.preview_start = Date.now();

        // randomly select preview time
        const preview_times = trial_config.value.preview_times;
        selected_preview_time.value = preview_times[Math.floor(Math.random() * preview_times.length)];

        preview_timer.start(selected_preview_time.value, () => {
          state_machine.transitionTo(trial_state.prospective);
        });
      },
      onExit: () => {
        preview_timer.stop();
        trial_timestamps.value.preview_end = Date.now();
      },
    },
    [trial_state.prospective]: {
      canTransitionTo: [trial_state.solving],
      canTransition: () => can_proceed_from_prospective.value,
      onEnter: () => {
        console.log("entered prospective phase");
        trial_timestamps.value.prospective_start = Date.now();
      },
      onExit: () => {
        trial_timestamps.value.prospective_end = Date.now();
      },
    },
    [trial_state.solving]: {
      canTransitionTo: [trial_state.retrospective],
      onEnter: () => {
        console.log("entered solving phase");
        trial_timestamps.value.solving_start = Date.now();

        // randomly select time limit
        const time_limits = trial_config.value.time_limits;
        selected_time_limit.value = time_limits[Math.floor(Math.random() * time_limits.length)];

        solving_timer.start(selected_time_limit.value, () => {
          state_machine.transitionTo(trial_state.retrospective);
        });
      },
      onExit: () => {
        solving_timer.stop();
        trial_timestamps.value.solving_end = Date.now();
      },
    },
    [trial_state.retrospective]: {
      canTransitionTo: [trial_state.complete],
      canTransition: () => can_proceed_from_retrospective.value,
      onEnter: () => {
        console.log("entered retrospective phase");
        trial_timestamps.value.retrospective_start = Date.now();
      },
      onExit: () => {
        trial_timestamps.value.retrospective_end = Date.now();
      },
    },
    [trial_state.complete]: {
      onEnter: () => {
        console.log("trial complete - saving data");

        // calculate performance
        const correct_cells = pc.get_correct_cells?.() || [];
        const incorrect_cells = pc.get_incorrect_cells?.() || [];
        const points = correct_cells.length * 2; // same scoring as original

        // record trial completion using experiment store
        if (executor?.value?.data_collection) {
          executor.value.data_collection.record_trial_end(
            null,
            correct_cells.length > 0, // success if any cells correct
            points,
            {
              final_board: pc.state_puzzle.value.board,
              correct_cells_count: correct_cells.length,
              incorrect_cells_count: incorrect_cells.length,
              selected_preview_time: selected_preview_time.value,
              selected_time_limit: selected_time_limit.value,
              prospective_estimates: prospective_responses.value.estimates,
              prospective_confidence: prospective_responses.value.confidence,
              retrospective_estimate: retrospective_responses.value.estimate,
              retrospective_confidence: retrospective_responses.value.confidence,
              initial_unmarked_cells: number_of_initial_unmarked_cells,
              final_marked_cells: currently_marked_cells.value,
              correct_marked_cells: current_correctly_marked_cells.value,
              timestamps: trial_timestamps.value,
            },
          );

          // record points in executor
          executor.value.data_collection.add_points(points, "trial_completion", props.trial_index);
        }

        emit("trial-complete");
      },
    },
  },
});

// response handlers
function update_prospective_estimate(time: number, estimate: number) {
  prospective_responses.value.estimates[time] = estimate;
}

function update_retrospective_estimate(estimate: number) {
  retrospective_responses.value.estimate = estimate;
}

const can_finish_solving_early = computed(() => {
  if (!pc.state_puzzle.value.board || state_machine.current_state.value !== trial_state.solving) return;
  const unmarked_count = pc.state_puzzle.value.board.flat().filter((cell) => cell === MinesweeperCell.UNMARKED).length;
  return unmarked_count === 0;
});


onUnmounted(() => {
  preview_timer.stop();
  solving_timer.stop();
});

onMounted(() => {
  state_machine.reset();
  if (executor?.value?.data_collection) {
    executor.value.data_collection.record_trial_start(props.trial_index, props.stimulus_item);
  }
});
</script>

<template>
  <div class="metacognition-trial mx-auto w-full pb-2 max-w-prose">
    <!-- preview phase -->
    <div v-if="state_machine.current_state.value === trial_state.preview" class="text-2xl text-center flex flex-col">
      <div class="font-mono">{{ preview_timer.time_remaining.value }}</div>
      <div class="text-sm text-gray-600 mb-4">Mark the board</div>

      <div class="flex flex-col items-center">
        <div class="p-2 flex flex-col mt-4 border rounded-lg shadow">
          <PuzzleRenderer :definition="puzzle" :state="pc.state_puzzle.value" :scale="1" :interact="bridge" />
        </div>
      </div>
    </div>

    <!-- prospective judgment phase -->
    <div v-else-if="state_machine.current_state.value === trial_state.prospective" class="flex flex-col gap-5">
      {{prospective_responses}}
      <div class="text-xl">
        <p>
          There were <span class="font-bold">{{ number_of_initial_unmarked_cells }} unknown cells</span>
          on the board you just saw.
        </p>
        <p>
          You marked <span class="font-bold">{{ currently_marked_cells }} </span> out of those
          <span class="font-bold">{{ number_of_initial_unmarked_cells }}</span> unknown cells so far.
        </p>
      </div>

      <Container v-if="currently_marked_cells > 0" class="flex flex-row gap-5">
        <div class="flex-1 text-xl">How many cells do you think you've correctly marked so far?</div>
        <NumberField
          :min="0"
          :max="currently_marked_cells"
          v-model="prospective_responses.estimates[0]"
          class="h-full flex flex-row"
        >
          <NumberFieldContent class="w-25">
            <NumberFieldDecrement />
            <NumberFieldInput class="text-xl" />
            <NumberFieldIncrement />
          </NumberFieldContent>
        </NumberField>
        <div class="mt-1 text-nowrap text-xl">of {{ currently_marked_cells }}</div>
      </Container>
      <div v-else class="hidden">
        {{ prospective_responses.estimates[0] = 0 }}
      </div>

      <div class="flex flex-col flex-1 text-xl gap-5">
        <Container>
          <div>
            Out of all <span class="font-bold">{{ number_of_initial_unmarked_cells }} unknown cells</span>, how many do
            you think you can identify correctly if you continued playing for...
          </div>

          <div class="grid grid-cols-3 gap-5 mt-2">
            <div
              v-for="time in trial_config.prediction_times"
              :key="time"
              class="gap-5 border-1 p-1 rounded bg-slate-100 shadow"
            >
              <div class="flex-1 text-xl">
                <span class="text-blue-500">{{ time }}</span> more seconds?
              </div>
              <NumberField
                :min="1"
                :max="number_of_initial_unmarked_cells"
                :model-value="prospective_responses.estimates[time]"
                @update:model-value="(val) => update_prospective_estimate(time, val)"
                class="w-full flex flex-row"
              >
                <NumberFieldContent class="w-25">
                  <NumberFieldDecrement />
                  <NumberFieldInput class="text-xl" />
                  <NumberFieldIncrement />
                </NumberFieldContent>
                <div class="mt-1 text-nowrap">of {{ number_of_initial_unmarked_cells }}</div>
              </NumberField>
            </div>
          </div>
        </Container>
      </div>

      <Container class="text-xl">
        <div>How confident are you in your estimates?</div>
        <div class="flex flex-row gap-3 mt-2 text-lg">
          <ExperimentInputSlider
            :labels="['Completely Unsure', 'Completely Sure']"
            class="px-15"
            v-model="prospective_responses.confidence"
          />
        </div>
      </Container>

      <Button
        variant="default"
        :disabled="!can_proceed_from_prospective"
        @click="() => state_machine.transitionTo(trial_state.solving)"
      >
        Continue
      </Button>
    </div>

    <!-- solving phase -->
    <div v-else-if="state_machine.current_state.value === trial_state.solving" class="text-2xl text-center">
      <div class="font-mono">{{ solving_timer.time_remaining.value }}</div>
      <div class="text-sm text-gray-600 mb-4 italic">Time limit: {{ selected_time_limit }} seconds</div>

      <div class="flex flex-col items-center">
        <div class="p-2 flex flex-col mt-4 border rounded-lg shadow">
          <PuzzleRenderer :definition="puzzle" :state="pc.state_puzzle.value" :scale="1" :interact="bridge" />
        </div>
      </div>

      <Button
        variant="default"
        v-if="can_finish_solving_early"
        @click="() => state_machine.transitionTo(trial_state.retrospective)"
        class="mt-2"
      >
        Continue
      </Button>
    </div>

    <!-- retrospective judgment phase -->
    <div v-else-if="state_machine.current_state.value === trial_state.retrospective" class="flex flex-col gap-5">
      {{retrospective_responses}}
      {{can_proceed_from_retrospective}}

      <div class="text-xl">
        <p>
          There were <span class="font-bold">{{ number_of_initial_unmarked_cells }} unknown cells</span>
          on the board you just saw.
        </p>
        <p>
          You marked <span class="font-bold">{{ currently_marked_cells }}</span> out of those
          <span class="font-bold">{{ number_of_initial_unmarked_cells }}</span> unknown cells.
        </p>
      </div>

      <Container class="flex flex-row gap-5 text-xl">
        <div class="flex-1">How many cells do you think you answered correctly?</div>
        <NumberField
          :min="0"
          :max="currently_marked_cells"
          :model-value="retrospective_responses.estimate"
          @update:model-value="update_retrospective_estimate"
          class="h-full flex flex-row"
        >
          <NumberFieldContent class="w-25">
            <NumberFieldDecrement />
            <NumberFieldInput class="text-xl" />
            <NumberFieldIncrement />
          </NumberFieldContent>
          <div class="mt-1 text-nowrap">of {{ currently_marked_cells }}</div>
        </NumberField>
      </Container>

      <Container>
        <div>How confident are you in your estimate?</div>
        <div class="flex flex-row gap-3 mt-2 text-lg">
          <ExperimentInputSlider
            :labels="['Completely Unsure', 'Completely Sure']"
            class="px-15"
            v-model="retrospective_responses.confidence"
          />
        </div>
      </Container>

      <Button
        variant="default"
        :disabled="!can_proceed_from_retrospective"
        @click="() => state_machine.transitionTo(trial_state.complete)"
      >
        Continue
      </Button>
    </div>

    <!-- error state -->
    <div v-else>Unknown state: {{ state_machine.current_state.value }}</div>
  </div>
</template>

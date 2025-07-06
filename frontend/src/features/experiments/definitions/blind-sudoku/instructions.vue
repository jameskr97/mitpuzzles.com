<script setup lang="ts">
import { type PropType, ref } from "vue";
import type { ExperimentContext } from "@/features/experiments/core/types.ts";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { getPersistentHighlightSudokuBoard } from "@/features/games/sudoku/getPersistentHighlightSudokuBoard.ts";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import { useDemoSudokuController } from "@/features/games/sudoku/useDemoSudokuController.ts";
import { Alert, AlertTitle } from "@/components/ui/alert";
import Quiz from "@/features/experiments/components/Quiz.vue";
import Container from "@/components/ui/Container.vue";
import { useExperimentContext } from "@/features/experiments/core/useExperimentContext.ts";
import { shuffle } from "@/utils.ts";

const props = defineProps({
  context: {
    type: Object as PropType<ExperimentContext>,
    required: true,
  },
});

const c = useExperimentContext();
const def: Partial<PuzzleDefinition> = {
  rows: 9,
  cols: 9,
  initial_state: [
    [1, 5, 6, 0, 8, 0, 0, 2, 0],
    [0, 0, 0, 1, 2, 0, 6, 5, 0],
    [3, 4, 2, 6, 0, 5, 0, 0, 1],
    [0, 8, 5, 0, 0, 3, 0, 4, 0],
    [4, 0, 0, 2, 0, 0, 8, 7, 5],
    [0, 7, 9, 4, 0, 8, 3, 1, 0],
    [0, 0, 0, 0, 3, 1, 4, 0, 2],
    [9, 2, 4, 5, 0, 6, 1, 3, 8],
    [8, 3, 1, 0, 4, 0, 0, 0, 7],
  ],
};

// prettier-ignore
const gameState0: PuzzleState = {
  // @ts-expect-error partial definition
  definition: def,
  board: [
    [1, 5, 6, 0, 8, 0, 0, 2, 0],
    [0, 0, 0, 1, 2, 0, 6, 5, 0],
    [3, 4, 2, 6, 0, 5, 0, 0, 1],
    [0, 8, 5, 0, 0, 3, 0, 4, 0],
    [4, 0, 0, 2, 0, 0, 8, 7, 5],
    [0, 7, 9, 4, 0, 8, 3, 1, 0],
    [0, 0, 0, 0, 3, 1, 4, 0, 2],
    [9, 2, 4, 5, 0, 6, 1, 3, 8],
    [8, 3, 1, 0, 4, 0, 0, 0, 7]
  ]
};

const gameState0With8: PuzzleState = {
  // @ts-expect-error partial definition
  definition: def,
  board: [
    [1, 5, 6, 0, 8, 0, 0, 2, 0],
    [0, 0, 0, 1, 2, 0, 6, 5, 0],
    [3, 4, 2, 6, 0, 5, 0, 8, 1],
    [0, 8, 5, 0, 0, 3, 0, 4, 0],
    [4, 0, 0, 2, 0, 0, 8, 7, 5],
    [0, 7, 9, 4, 0, 8, 3, 1, 0],
    [0, 0, 0, 0, 3, 1, 4, 0, 2],
    [9, 2, 4, 5, 0, 6, 1, 3, 8],
    [8, 3, 1, 0, 4, 0, 0, 0, 7],
  ],
};

const gameState0Solution: PuzzleState = {
  // @ts-expect-error partial definition
  definition: def,
  board: [
    [1, 5, 6, 3, 8, 7, 9, 2, 4],
    [7, 9, 8, 1, 2, 4, 6, 5, 3],
    [3, 4, 2, 6, 9, 5, 7, 8, 1],
    [6, 8, 5, 7, 1, 3, 2, 4, 9],
    [4, 1, 3, 2, 6, 9, 8, 7, 5],
    [2, 7, 9, 4, 5, 8, 3, 1, 6],
    [5, 6, 7, 8, 3, 1, 4, 9, 2],
    [9, 2, 4, 5, 7, 6, 1, 3, 8],
    [8, 3, 1, 9, 4, 2, 5, 6, 7],
  ],
};

const { puzzle_state: demo_puzzle_state, interact: demo_interact } = useDemoSudokuController(def, {
  cycle_mode: false,
  allow_prefilled_modification: false,
});

const CANDIDATE_CLASS = "border-3! border-amber-500!";
const RowHighlighted = getPersistentHighlightSudokuBoard({
  row: 2,
  cells: [
    { row: 2, col: 4 },
    { row: 2, col: 6 },
    { row: 2, col: 7 },
  ],
  highlight_cells: [
    { row: 2, col: 4, classStyle: CANDIDATE_CLASS },
    { row: 2, col: 6, classStyle: CANDIDATE_CLASS },
    { row: 2, col: 7, classStyle: CANDIDATE_CLASS },
  ],
});
const ColHighlighted = getPersistentHighlightSudokuBoard({
  col: 6,
  cells: [
    { row: 0, col: 6 },
    { row: 2, col: 6 },
    { row: 3, col: 6 },
    { row: 3, col: 6 },
    { row: 8, col: 6 },
  ],
  highlight_cells: [
    { row: 2, col: 4, classStyle: CANDIDATE_CLASS },
    { row: 2, col: 7, classStyle: CANDIDATE_CLASS },
  ],
});
const BoxHighlighted = getPersistentHighlightSudokuBoard({
  box: 1,
  cells: [
    { row: 6, col: 0 },
    { row: 6, col: 1 },
    { row: 6, col: 2 },
  ],
  highlight_cells: [{ row: 2, col: 7, classStyle: CANDIDATE_CLASS }],
  specific_cell_class: [{ row: 2, col: 7, classStyle: "text-amber-500!" }],
});

const showQuizWarning = ref(false);
let quiz: { answer: boolean; question: string }[] =
  shuffle(
  [
    { answer: true, question: "Each row must have the numbers 1 to 9, with no repeats." },
    { answer: true, question: "Each column must include every number from 1 to 9 exactly once." },
    { answer: true, question: "Each 3x3 box must include every number from 1 to 9 exactly once." },
    { answer: false, question: "You can use the same number multiple times in a column." },
    { answer: false, question: "A 3x3 box can include the same number multiple times." },
    { answer: false, question: "The starting numbers can be changed." },
    { answer: false, question: "I will be able to see the entire board at once." }
  ]
);

function onQuizSubmitted(allCorrect: boolean) {
  if (allCorrect) {
    c.nextStep();
  } else {
    showQuizWarning.value = true;
  }
}
</script>

<template>
  <div class="container contents-main-wrapper mx-auto max-w-[78ch] flex flex-col prose">
    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary my-2">Game Overview</h3>

    <div>
      <p>
        Sudoku is a logic puzzle played on a grid. The grid is divided into 9 rows and 9 columns, forming 9 smaller
        grids (3x3 squares). In order to solve a sudoku board, every square must be filled in with a number from 1 to 9.
        Some numbers are already filled in when you start, and they cannot be changed.
      </p>
      <p>
        Your job is figuring out which numbers go into the empty squares by looking at numbers that are already filled
        in the row, column, or 3x3 squares.
      </p>
      <p>However, there are some important rules around how many times you can use each number!</p>
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary my-2">Sudoku Rules</h3>

    <div class="grid grid-cols-[auto_min-content] gap-x-5 gap-y-10 w-full">
      <div class="grid col-span-2 grid-cols-subgrid">
        <div class="flex flex-col gap-1">
          <div>
            First, each <strong>row</strong> must include every number from 1 to 9, and each number must appear exactly
            <strong>once</strong>.
          </div>
          <div class="italic">
            The highlighted row has the numbers 3, 4, 2, 6, 5, and 1. It needs the numbers 7, 8, and 9 for the row to be
            complete.
          </div>
          <Container class="border-black/10 bg-amber-500/20! border-1">
            <div>
              For example, 8 could be in any one of the locations
              <span class="font-bold">highlighted with an orange border</span>.
            </div>
          </Container>
        </div>
        <RowHighlighted :state="gameState0" :scale="0.75"></RowHighlighted>
      </div>

      <div class="grid col-span-2 grid-cols-subgrid">
        <div class="flex flex-col gap-4">
          <div>
            Second, each <strong>column</strong> must include every number from 1 to 9, and each number must appear
            exactly <strong>once</strong>.
          </div>
          <div class="italic">
            The highlighted row has the numbers 6, 8, 3, 4, and 1. It needs the numbers 2, 5, 7, and 9 for the column to
            be complete.
          </div>
          <Container class="border-black/10 bg-amber-500/20! border-1">
            <div>
              Since the highlighted column already contains an 8, this column is
              <span class="font-bold">ruled out</span>
              as a possible location for 8 in the third row.
            </div>
          </Container>
        </div>
        <ColHighlighted :state="gameState0" :scale="0.75"></ColHighlighted>
      </div>

      <div class="grid col-span-2 grid-cols-subgrid">
        <div class="flex flex-col gap-4">
          <div>
            Third, each <strong>box</strong> must include every number from 1 to 9, and each number must appear exactly
            <strong>once</strong>.
          </div>
          <div class="italic">
            The highlighted box has the numbers 9, 2, 4, 8, 3, and 1. It needs the numbers 5, 6, and 7 for the box to be
            complete.
          </div>
          <Container class="border-black/10 bg-amber-500/20! border-1">
            <div>
              Since the highlighted box already contains an 8, it rules out one more location for 8 in the third row.
              This allows us <span class="font-bold">to deduce the correct location for 8 in the third row</span>.
            </div>
          </Container>
        </div>
        <BoxHighlighted :state="gameState0With8" :scale="0.75"></BoxHighlighted>
      </div>
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary pb-2 mb-4">Additional Challenge</h3>
    <p>
      In addition to the standard Sudoku rules explained above,
      <span class="font-bold">
        you will never be able to see the full board at once, but only a part it at any given time.
      </span>
      Below we explain to you how you can interact with the board to change what you can see.
    </p>

    <h4 class="text-xl font-medium text-slate-700 mt-8">How to interact with the board:</h4>

    <ul class="text-lg">
      <li><strong>Hover:</strong> Move your mouse over the board to preview which area to reveal.</li>
      <li>
        <strong>Reveal:</strong> Click on a cell to reveal that cell
        <div class="inline-block h-5 w-5 bg-slate-300 rounded border-1 border-black/40"></div>
        (dark blue) and the row, column, and box which it belongs to (light blue)
        <div class="inline-block h-5 w-5 bg-slate-200 rounded border-1 border-black/40"></div>
        .
      </li>
      <li>
        <strong>Input:</strong> Enter a number in the selected cell (dark blue) by pressing number keys 1 to 9 on your
        keyboard. Numbers you entered will appear in <span class="text-sky-600 font-bold">blue</span>, and can be
        changed again later.
      </li>
    </ul>
    <div class="flex flex-col w-full items-center">
      <div class="alert alert-info mb-4">Try using the board below to see how it will work!</div>
      <PuzzleSudoku :state="demo_puzzle_state" :scale="1" :interact="demo_interact" />
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-secondary pb-2 mb-4">Scoring</h3>
    <div class="mb-4">
      <p>
        <span class="font-bold">You will be asked to solve 3 boards.</span> You will be able to earn a bonus depending
        on your performance. Each correct number <span class="font-bold">will earn you 3 points.</span> Any incorrect
        cell loses you 3 points. Each point is worth $0.01 (e.g. 100 points would earn you $1.00)
      </p>
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-secondary pb-2 mb-4">Comprehension Quiz</h3>
    <div>
      <p>
        Please answer these brief comprehension questions before beginning the experiment. Check which of the following
        statements about the game are true:
      </p>
      <Alert v-if="showQuizWarning" variant="warning">
        <AlertTitle>Please double check your answers</AlertTitle>
      </Alert>
      <Quiz :questions="quiz" @eval-result="(args) => onQuizSubmitted(args)" />
    </div>
  </div>
</template>

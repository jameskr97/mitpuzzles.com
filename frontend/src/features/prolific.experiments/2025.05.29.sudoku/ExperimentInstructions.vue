<script setup lang="ts">
import { type PropType, ref } from "vue";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import Quiz from "@/features/prolific.components/Quiz.vue";
import { getPersistentHighlightSudokuBoard } from "@/features/games/sudoku/getPersistentHighlightSudokuBoard.ts";
import { Alert, AlertTitle } from "@/components/ui/alert";
import { useExperimentController } from "@/features/prolific.composables/useExperimentController.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { withSudokuFocusBehavior } from "@/features/games/sudoku/useSudokuFocusHighlighter.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import { useRoute } from "vue-router";



const props = defineProps({
  context: {
    type: Object as PropType<ReturnType<typeof useExperimentController>>,
    required: true,
  },
});
const route = useRoute();
const ec = useExperimentController(route.meta.experiment_key as string);

// prettier-ignore
const gameState0 = ref<PuzzleStateSudoku>(
  {
    "rows": 9,
    "cols": 9,
    "board": [1, 5, 6, 0, 8, 0, 0, 2, 0, 0, 0, 0, 1, 2, 0, 6, 5, 0, 3, 4, 2, 6, 0, 5, 0, 0, 1, 0, 8, 5, 0, 0, 3, 0, 4, 0, 4, 0, 0, 2, 0, 0, 8, 7, 5, 0, 7, 9, 4, 0, 8, 3, 1, 0, 0, 0, 0, 0, 3, 1, 4, 0, 2, 9, 2, 4, 5, 0, 6, 1, 3, 8, 8, 3, 1, 0, 4, 0, 0, 0, 7],
    "board_initial": [1, 5, 6, 0, 8, 0, 0, 2, 0, 0, 0, 0, 1, 2, 0, 6, 5, 0, 3, 4, 2, 6, 0, 5, 0, 0, 1, 0, 8, 5, 0, 0, 3, 0, 4, 0, 4, 0, 0, 2, 0, 0, 8, 7, 5, 0, 7, 9, 4, 0, 8, 3, 1, 0, 0, 0, 0, 0, 3, 1, 4, 0, 2, 9, 2, 4, 5, 0, 6, 1, 3, 8, 8, 3, 1, 0, 4, 0, 0, 0, 7],
    "puzzle_type": "sudoku",
    "puzzle_size": "9x9",
    "puzzle_difficulty": "hard",
    "session_id": "static-session-3430",
    "violations": [],
    "is_solved": false
  }
);

// prettier-ignore
const gameState0Solution = ref<PuzzleStateSudoku>(
  {
    "rows": 9,
    "cols": 9,
    "board": [1, 5, 6, 3, 8, 7, 9, 2, 4, 7, 9, 8, 1, 2, 4, 6, 5, 3, 3, 4, 2, 6, 9, 5, 7, 8, 1, 6, 8, 5, 7, 1, 3, 2, 4, 9, 4, 1, 3, 2, 6, 9, 8, 7, 5, 2, 7, 9, 4, 5, 8, 3, 1, 6, 5, 6, 7, 8, 3, 1, 4, 9, 2, 9, 2, 4, 5, 7, 6, 1, 3, 8, 8, 3, 1, 9, 4, 2, 5, 6, 7],
    "board_initial": [1, 5, 6, 0, 8, 0, 0, 2, 0, 0, 0, 0, 1, 2, 0, 6, 5, 0, 3, 4, 2, 6, 0, 5, 0, 0, 1, 0, 8, 5, 0, 0, 3, 0, 4, 0, 4, 0, 0, 2, 0, 0, 8, 7, 5, 0, 7, 9, 4, 0, 8, 3, 1, 0, 0, 0, 0, 0, 3, 1, 4, 0, 2, 9, 2, 4, 5, 0, 6, 1, 3, 8, 8, 3, 1, 0, 4, 0, 0, 0, 7],
    "puzzle_id": 3430,
    "puzzle_type": "sudoku",
    "puzzle_size": "9x9",
    "puzzle_difficulty": "hard"
  }
);

const puzzle = await usePuzzleController("sudoku", { mode: "local", initialState: gameState0 });
const bridge = await createPuzzleInteractionBridge("sudoku", { mode: "local", state: puzzle.state });
withSudokuBehaviors(puzzle, bridge);
withSudokuFocusBehavior(puzzle, bridge);

const RowHighlighted = getPersistentHighlightSudokuBoard({
  row: 2,
  cells: [
    { row: 2, col: 4 },
    { row: 2, col: 6 },
    { row: 2, col: 7 },
  ],
});
const ColHighlighted = getPersistentHighlightSudokuBoard({
  col: 2,
  cells: [
    { row: 1, col: 2 },
    { row: 4, col: 2 },
    { row: 6, col: 2 },
  ],
});
const BoxHighlighted = getPersistentHighlightSudokuBoard({
  box: 6,
  cells: [
    { row: 6, col: 0 },
    { row: 6, col: 1 },
    { row: 6, col: 2 },
  ],
});

const showQuizWarning = ref(false);
let quiz: { answer: boolean; question: string }[] =
  /*shuffle(*/
  [
  { answer: true, question: "Each row must have the numbers 1 to 9, with no repeats." },
  { answer: true, question: "Each column must include every number from 1 to 9 exactly once." },
  { answer: true, question: "Each 3x3 box must include every number from 1 to 9 exactly once." },
  { answer: false, question: "You can use the same number multiple times in a column." },
  { answer: false, question: "A 3x3 box can include the same number multiple times." },
  { answer: false, question: "The starting numbers can be changed." },
];
  //);

function onQuizSubmitted(allCorrect: boolean) {
  if (allCorrect) {
    ec.nextStep()
  } else {
    showQuizWarning.value = true;
  }
}
</script>

<template>
  <div class="container contents-main-wrapper mx-auto max-w-prose flex flex-col prose">
    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary my-2">Game Overview</h3>

    <div>
      Sudoku is a logic puzzle played on a square. The square is divided into 9 rows and 9 columns, forming 9 smaller
      squares (3x3). In order to solve a sudoku board, every empty square must be filled in with a number from 1 to 9,
      but there are some rules around how many times you can use each number.
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary my-2">Sudoku Rules</h3>

    <div class="grid grid-cols-2 w-full gap-5">
      <div class="flex flex-col gap-4 row-start-1">
        <div>
          Each <strong>row</strong> must include each number 1 to 9, and each number can appear exactly once.
          <strong>once</strong>.
        </div>
        <div class="italic">
          The highlighted row has the numbers 3, 4, 2, 6, 5, and 1. It needs the numbers 7, 8, and 9 for the row to be
          complete.
        </div>
      </div>
      <RowHighlighted :state="gameState0" :scale="0.75"></RowHighlighted>

      <div class="flex flex-col gap-4 row-start-2">
        <div>
          Each <strong>column</strong> must include each number 1 to 9, and each number can appear exactly once.
          <strong>once</strong>.
        </div>
        <div class="italic">
          The highlighted row has the numbers 1, 4, 9, 5, 2, and 6. It needs the numbers 3, 7, and 8 for the column to
          be complete.
        </div>
      </div>
      <ColHighlighted :state="gameState0" :scale="0.75"></ColHighlighted>

      <div class="flex flex-col gap-4 row-start-3">
        <div>
          Each <strong>box</strong> must include each number 1 to 9, and each number can appear exactly once.
          <strong>once</strong>.
        </div>
        <div class="italic">
          The highlighted box has the numbers 9, 2, 4, 8, 3, and 1. It needs the numbers 5, 6, and 7 for the box to be
          complete.
        </div>
      </div>
      <BoxHighlighted :state="gameState0" :scale="0.75"></BoxHighlighted>
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary m-0 p-0"></h3>

    <ul>
      <li>
        Some numbers are already filled in when you start. You cannot change those numbers. They are there to give you
        clues for what numbers should be filled in the empty spaces.
      </li>
      <li>
        Your job is to figure out the missing numbers by looking at what is already in the row, column, or box, and
        finding numbers that can fit in the open spaces, without breaking any of the rules above.
      </li>
    </ul>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-primary pb-2 mb-4">Additional Challenge</h3>
    <p>In addition to the typical sudoku rules, you will also be restricted from seeing the full board.</p>

    <h4 class="text-xl font-medium text-slate-700 mt-8">How to interact with the board:</h4>

    <ul>
      <li><strong>Hover:</strong> Move your mouse over the board to see a highlighted section.</li>
      <li><strong>Select:</strong> Click on a cell to select it. This click will also reveal the highlighted area.</li>
      <li>
        <strong>Input:</strong> Press number keys
        <kbd class="kbd kbd-md">1</kbd>
        to
        <kbd class="kbd kbd-md">9</kbd>
        answer in the selected cell
      </li>
    </ul>
    <div class="flex flex-col w-full items-center">
      <div class="alert alert-info mb-4">Try using the board below to see how it will work!</div>
      <PuzzleSudoku :state="gameState0" :scale="1" :interact="bridge" />
    </div>

    <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-secondary pb-2 mb-4">Scoring</h3>
    <div class="mb-4">
      <p>
        You will be asked to solve <span class="font-bold">5</span> boards. You will be able to earn a bonus depending
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

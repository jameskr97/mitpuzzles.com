<script setup lang="ts">
import { inject, type Ref, ref, computed } from "vue";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types";
import { getPersistentHighlightSudokuBoard } from "@/features/games/sudoku/getPersistentHighlightSudokuBoard.ts";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import { useDemoSudokuController } from "@/features/games/sudoku/useDemoSudokuController.ts";
import { Alert, AlertTitle } from "@/components/ui/alert";
import ExperimentQuiz from "@/features/experiment-core/components/ExperimentQuiz.vue";
import Container from "@/components/ui/Container.vue";
import { shuffle } from "@/utils.ts";
import { GraphExecutor } from "@/features/experiment-core";
import { Button } from "@/components/ui/button";
import InstructionHeader from "@/features/experiment-core/components/InstructionHeader.vue";

const executor = inject<Ref<GraphExecutor>>("experiment-executor");

// detect visitor type from data collection
const is_prolific_visitor = computed(() =>
  executor?.value?.data_collection?.participant_data?.recruitment_platform === "prolific"
);

const is_direct_visitor = computed(() => !is_prolific_visitor.value);

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
let quiz: { answer: boolean; question: string }[] = shuffle([
  { answer: true, question: "Each row must have the numbers 1 to 9, with no repeats." },
  { answer: true, question: "Each column must include every number from 1 to 9 exactly once." },
  { answer: true, question: "Each 3x3 box must include every number from 1 to 9 exactly once." },
  { answer: false, question: "You can use the same number multiple times in a column." },
  { answer: false, question: "A 3x3 box can include the same number multiple times." },
  { answer: false, question: "The starting numbers can be changed." },
  { answer: false, question: "I will be able to see the entire board at once." },
]);
</script>

<template>
  <Container class="max-w-[75ch] flex flex-col">
    <InstructionHeader>Game Overview</InstructionHeader>

    <div class="flex flex-col gap-5">
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

    <InstructionHeader>Sudoku Rules</InstructionHeader>

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
            The highlighted column has the numbers 6, 8, 3, 4, and 1. It needs the numbers 2, 5, 7, and 9 for the column
            to be complete.
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
            The highlighted box has the numbers 8, 1, 2, 6, and 5. It needs the numbers 3, 4, 7 and 9 for the box to be
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

    <InstructionHeader>Additional Challenge</InstructionHeader>
    <p>
      In addition to the standard Sudoku rules explained above,
      <span class="font-bold">
        you will never be able to see the full board at once, but only a part of it at any given time.
      </span>
      Below we explain how you can interact with the board.
    </p>

    <InstructionHeader class="border-dashed text-xl">How to interact with the board:</InstructionHeader>

    <ul class="list-disc ml-4">
      <li><strong>Hover:</strong> Move your mouse over the board to preview which area to reveal.</li>
      <li>
        <strong>Reveal:</strong> Click on a cell to reveal that cell
        <div class="inline-block h-5 w-5 bg-slate-300 rounded border-1 border-black/40"></div>
        (dark blue) and the row, column, and box which it belongs to (light blue)
        <div class="inline-block h-5 w-5 bg-slate-200 rounded border-1 border-black/40"></div>.
      </li>
      <li>
        <strong>Input:</strong> Enter a number in the selected cell (dark blue) by pressing number keys 1 to 9 on your
        keyboard. Numbers you entered will appear in <span class="text-sky-600 font-bold">blue</span>, and can be
        changed again later.
      </li>
    </ul>
    <Container class="flex flex-col items-center max-w-fit mx-auto my-4">
      <div class="alert alert-info mb-4">Try using the board below to see how it will work!</div>
      <PuzzleSudoku :state="demo_puzzle_state" :scale="1" :interact="demo_interact" />
    </Container>

    <!-- scoring section only for prolific users -->
    <div v-if="is_prolific_visitor">
      <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-secondary pb-2 mb-4">Scoring</h3>
      <div class="mb-4">
        <p>
          <span class="font-bold">You will be asked to solve {{ executor?.total_trial_count }} boards.</span> You will be able to earn a bonus depending
          on your performance. Each correct number <span class="font-bold">will earn you 2 points.</span> Any incorrect
          cell loses you 2 points. Each point is worth $0.01 (e.g. 100 points would earn you $1.00)
        </p>
      </div>
    </div>

    <!-- For Prolific visitors: show comprehension quiz -->
    <div v-if="is_prolific_visitor">
      <h3 class="text-2xl font-semibold text-slate-700 border-b-2 border-b-secondary pb-2 mb-4">Comprehension Quiz</h3>
      <div>
        <p>
          Please answer these brief comprehension questions before beginning the experiment. Check which of the following
          statements about the game are true:
        </p>
        <Alert v-if="showQuizWarning" variant="warning">
          <AlertTitle>Please double check your answers</AlertTitle>
        </Alert>

        <ExperimentQuiz :questions="quiz" @onCorrect="$emit('complete')" />
      </div>
    </div>

    <!-- For direct visitors: show consent text and skip quiz -->
    <div v-if="is_direct_visitor">
      <InstructionHeader>We need your consent to proceed</InstructionHeader>
      <div class="flex flex-col gap-4 p-4 border rounded-lg bg-gray-50">
        <p>By completing this study, you are participating in a study being performed by
        cognitive scientists in the MIT Department of Brain and Cognitive Science.
        The purpose of this research is to understand how people reason and solve problems.</p>

        <p>You must be at least 18 years old to participate. There are neither specific benefits nor
        anticipated risks associated with participation in this study. Your participation in this
        study is completely voluntary, and you can withdraw at any time by simply exiting the study.
        You may decline to answer any or all of the following questions. Choosing not to participate
        or withdrawing will result in no penalty. Your anonymity is assured; the researchers who have
        requested your participation will not receive any personal information about you, and any
        information you provide will not be shared in association with any personally identifying information.</p>

        <p>If you have questions about this research, please contact the researchers by sending an email to
        <a href="mailto:support@mitpuzzles.com" class="text-blue-600 underline">support@mitpuzzles.com</a>. These researchers will do their best to communicate with you in a timely,
        professional, and courteous manner. If you have questions regarding your rights as a research subject,
        or if problems arise which you do not feel you can discuss with the researchers, please contact the
        MIT Institutional Review Board.</p>

        <p>Your participation in this research is voluntary.
        You may discontinue participation at any time during the research activity.
        You may print a copy of this consent form for your records.</p>

        <div class="text-center mt-6">
          <Button @click="$emit('complete')" variant="default" class="px-8 py-2">
            Continue
          </Button>
        </div>
      </div>
    </div>
  </Container>
</template>

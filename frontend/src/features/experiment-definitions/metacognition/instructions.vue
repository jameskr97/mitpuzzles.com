<script setup lang="ts">
import Container from "@/components/ui/Container.vue";
import InstructionHeader from "@/features/experiment-core/components/InstructionHeader.vue";
import PuzzleMinesweeper from "@/features/games/minesweeper/minesweeper.puzzle.vue";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { fromResearchFormat, MinesweeperCell } from "@/services/game/engines/translator.ts";
import ExperimentQuiz from "@/features/experiment-core/components/ExperimentQuiz.vue";
import { shuffle } from "@/utils.ts";
import { GraphExecutor } from "@/features/experiment-core";
import { type Ref, inject, computed } from "vue";
import { Button } from "@/components/ui/button";

const executor = inject<Ref<GraphExecutor>>('experiment-executor');
const emits = defineEmits(['complete'])

// detect visitor type from data collection
const is_prolific_visitor = computed(() =>
  executor?.value?.data_collection?.participant_data?.recruitment_platform === "prolific"
);

const is_direct_visitor = computed(() => !is_prolific_visitor.value);
const definition: PuzzleDefinition = {
  puzzle_type: "minesweeper",
  rows: 3,
  cols: 3,
  initial_state: [
    [1, -1, 2],
    [2, -1, -1],
    [-1, -1, 1],
  ],
};

const gameState1: PuzzleState = {
  definition,
  board: fromResearchFormat(
    [
      [-1, -1, 1],
      [-1, 3, 2],
      [2, -1, 1],
    ],
    "minesweeper",
  ),
};

const gameState2: PuzzleState = {
  definition,
  board: fromResearchFormat(
    [
      [1, -1, 2],
      [2, -1, -1],
      [-1, -1, 1],
    ],
    "minesweeper",
  ),
};
const gameState3 = JSON.parse(JSON.stringify(gameState2));
gameState3.board[0][1] = MinesweeperCell.FLAG;
gameState3.board[1][2] = MinesweeperCell.FLAG;
gameState3.board[2][0] = MinesweeperCell.FLAG;
gameState3.board[1][1] = MinesweeperCell.SAFE;
gameState3.board[2][1] = MinesweeperCell.SAFE;

let quiz: { answer: boolean; question: string }[] = shuffle([
  { answer: true, question: "Each board contains a different number of mines that I need to deduce." },
  { answer: true, question: "Each numbered cell tells you how many mines are in the 8 adjacent cells." },
  { answer: false, question: "I can click on unrevealed cells to reveal them and see what's underneath." },
  { answer: false, question: "I can change the numbers that are already shown on revealed cells." },
  { answer: true, question: "Left-click cycles through flag, safe, and unmarked states on unrevealed cells." },
  { answer: false, question: "If a cell shows 3, there might be 2, 3, or 4 mines in the adjacent cells." },
  { answer: true, question: "Mines are in unrevealed cells that I must identify using logical deduction." },
]);
</script>

<template>
  <Container class="max-w-[75ch] mb-2 flex mx-auto">
    <InstructionHeader>Instructions</InstructionHeader>
    <div class="flex flex-col gap-5">
      <p>In this study, you will play a logic-puzzle variant of the well-known computer game Minesweeper.</p>
      <p>
        Minesweeper is a logic puzzle played on a grid where your goal is to identify the location of hidden mines. The
        grid contains numbered cells that provide clues about how many mines are adjacent (up, down, left, right, and
        diagonal) to that cell. Some cells contain mines, while others are safe. Your task is to use logical deduction
        to determine which cells contain mines and which are safe.
      </p>
    </div>
    <InstructionHeader>Game Overview</InstructionHeader>
    <div class="flex flex-col gap-5">
      <p>Here is an example of a 3x3 board.</p>
      <PuzzleMinesweeper :state="gameState1" class="mx-auto" />
      <p>
        The middle cell is marked <i class="md-cell minesweeper-cell-3"></i>. This means that three of the four adjacent
        squares have mines.
      </p>
    </div>

    <InstructionHeader>Goal</InstructionHeader>
    <p>
      Unlike in the classical game of Minesweeper, you will not be able to freely click on squares to reveal them. To
      "solve" a board, you must:
    </p>
    <ul class="list-disc ml-4">
      <li>
        <p>Place <b>flags</b> <i class="md-cell md-cell-flag"></i> on squares you suspect to be mines.</p>
      </li>
      <li>
        <p>Mark squares as <b>safe</b> <i class="md-cell md-cell-empty"></i> if you believe they're free of mines.</p>
      </li>
      <li>
        <u><i>Left-click</i> to cycle between flag and safe mark placements.</u> You can right-click to place a safe
        mark directly.
      </li>
    </ul>

    <InstructionHeader>Your Task</InstructionHeader>
    <div class="flex flex-col gap-2">
      <p>
        In the experiment, you will see 3x3 boards where not all squares have been revealed. Some unrevealed squares
        will have mines. Each trial has the following structure:
      </p>
      <ul class="list-decimal ml-4">
        <li>
          <span class="font-bold">Initial Play:</span>
          You will first see the board for <b>5 seconds</b>. During this time, begin solving the board by placing safe
          marks or flags on squares you believe are safe or contain mines, respectively.
        </li>
        <li>
          <p>After 5 seconds, the board will disappear. You will then be asked to estimate:</p>
          <ul class="list-decimal ml-8">
            <li>How many squares you have correctly identified <b>so far</b></li>
            <li>
              How many additional correct squares you think you <b>could</b> identify if given more time to continue for
              5, 10, and 30 seconds.
            </li>
          </ul>
        </li>
        <li>
          Once you submit your estimates, the board will reappear. You will then be given either 5, 10 or 30 seconds to
          solve the board. Use this time as you see fit to improve your solution.
        </li>
        <li>
          After the time is up, you will make a final estimate of how many squares you identified correctly overall,
          along with a confidence rating.
        </li>
      </ul>
    </div>

    <p>For instance, you might place flags and safe marks so that the board looks like the one shown below:</p>
    <PuzzleMinesweeper :state="gameState3" class="mx-auto" />

    <!-- scoring section only for prolific users -->
    <div v-if="is_prolific_visitor">
      <InstructionHeader>Scoring</InstructionHeader>
      <p>
        <span class="font-bold">You will be asked to solve {{ executor?.total_trial_count }} boards.</span> You will be able
        to earn a bonus depending on your performance. Each correct square
        <span class="font-bold">will earn you 1 point.</span> You cannot lose points for incorrect squares. Each point is
        worth $0.01 (e.g. 100 points would earn you $1.00)
      </p>
    </div>

    <!-- For Prolific visitors: show comprehension quiz -->
    <div v-if="is_prolific_visitor">
      <InstructionHeader>Comprehension Quiz</InstructionHeader>
      <ExperimentQuiz :questions="quiz" @on-correct="$emit('complete')" />
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
        <a href="mailto:cheyette@mit.edu" class="text-blue-600 underline">cheyette@mit.edu</a>. These researchers will do their best to communicate with you in a timely,
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

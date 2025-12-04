<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import InstructionHeader from "@/features/experiment-core/components/InstructionHeader.vue";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import { computed, inject, type Ref, ref } from "vue";
import ExperimentQuiz from "@/features/experiment-core/components/ExperimentQuiz.vue";
import { GraphExecutor } from "@/features/experiment-core";
import PuzzleSelector from "@/features/experiment-definitions/forced-choice/PuzzleSelector.vue";
import PuzzleRenderer from "@/core/components/PuzzleRenderer.vue";
import { Button } from "@/core/components/ui/button";

const executor = inject<Ref<GraphExecutor>>("experiment-executor");

// detect visitor type from data collection
const is_prolific_visitor = computed(
  () => executor?.value?.data_collection?.participant_data?.recruitment_platform === "prolific",
);

const is_direct_visitor = computed(() => !is_prolific_visitor.value);

const definition1: PuzzleDefinition = {
  puzzle_type: "minesweeper",
  rows: 3,
  cols: 3,
  initial_state: [
    [1, -1, 2],
    [2, -1, -1],
    [-1, -1, 1],
  ],
};

const definition2: PuzzleDefinition = {
  puzzle_type: "minesweeper",
  rows: 3,
  cols: 3,
  initial_state: [
    [-1, -1, 1],
    [-1, 3, 2],
    [2, -1, 1],
  ],
};

const selected_puzzle_index = ref<number | null>(null);
const can_proceed_to_solving = computed(() => selected_puzzle_index.value !== null);

let quiz: { answer: boolean; question: string }[] = [
  { answer: true, question: "When solving a board, your goal is to flag all the cells you suspect to have mines." },
  { answer: true, question: "Each numbered cell tells you how many mines are in the adjacent cells." },
  { answer: true, question: "Left-click cycles through flag, safe, and unmarked states on unrevealed cells." },
  { answer: true, question: "You should choose the board you think can be solved the quicklest." },
  { answer: false, question: "I can change the numbers that are already shown on revealed cells." },
  { answer: false, question: "I can click on unrevealed cells to reveal them and see what's underneath." },
  { answer: false, question: "If a cell shows 3, there might be 2, 3, or 4 mines in the adjacent cells." },
];
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
      <PuzzleRenderer :definition="definition2" class="mx-auto max-w-35 border border-[#767676]" />
      <p>
        The middle cell is marked <i class="md-cell minesweeper-cell-3"></i>. This means that three of the four adjacent
        squares have mines.
      </p>
    </div>

    <InstructionHeader>Game Rules</InstructionHeader>
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
        <u><i>Left-click to cycle forward, right-click to cycle backward</i> between flag and safe mark placements.</u>
      </li>
    </ul>

    <InstructionHeader>Your Task</InstructionHeader>
    <div class="flex flex-col gap-2">
      <p>
        There are <span class="font-bold">{{ executor?.total_trial_count }} trials</span> in this experiment. In each
        trial, you will be presented with a choice of two 3x3 minesweeper boards. Consider the two boards, and select
        the one you believe you can
        <span class="font-bold">solve the quickest.</span>
        Once you click the "Solve Selected Board" button, you will have to solve whichever board is currently selected.
      </p>

      <InstructionHeader></InstructionHeader>
      <div class="text-2xl text-center font-bold">Demo of Board Selection</div>
      <div class="text-center">Press your arrow key or click on a box to toggle between puzzles.</div>
      <div class="text-sm italic text-gray-500 text-center">
        You will have up to 30 seconds to view puzzles and make a selection.
        <br />
        The timer will start after you first view a puzzle.
        <br />
      </div>

      <Container class="my-4 py-4 border-5 border-caution-tape">
        <PuzzleSelector
          :puzzles="[definition1, definition2]"
          @selection-changed="(_from_index, to_index) => (selected_puzzle_index = to_index)"
        />
        <div class="text-center">
          <Button :disabled="!can_proceed_to_solving" class="mt-5" variant="default"> Solve Selected Puzzle </Button>
        </div>
      </Container>
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
        <p>
          By completing this study, you are participating in a study being performed by cognitive scientists in the MIT
          Department of Brain and Cognitive Science. The purpose of this research is to understand how people reason and
          solve problems.
        </p>

        <p>
          You must be at least 18 years old to participate. There are neither specific benefits nor anticipated risks
          associated with participation in this study. Your participation in this study is completely voluntary, and you
          can withdraw at any time by simply exiting the study. You may decline to answer any or all of the following
          questions. Choosing not to participate or withdrawing will result in no penalty. Your anonymity is assured;
          the researchers who have requested your participation will not receive any personal information about you, and
          any information you provide will not be shared in association with any personally identifying information.
        </p>

        <p>
          If you have questions about this research, please contact the researchers by sending an email to
          <a href="mailto:support@mitpuzzles.com" class="text-blue-600 underline">support@mitpuzzles.com</a>. These
          researchers will do their best to communicate with you in a timely, professional, and courteous manner. If you
          have questions regarding your rights as a research subject, or if problems arise which you do not feel you can
          discuss with the researchers, please contact the MIT Institutional Review Board.
        </p>

        <p>
          Your participation in this research is voluntary. You may discontinue participation at any time during the
          research activity. You may print a copy of this consent form for your records.
        </p>

        <div class="text-center mt-6">
          <Button @click="$emit('complete')" variant="default" class="px-8 py-2"> Continue </Button>
        </div>
      </div>
    </div>
  </Container>
</template>

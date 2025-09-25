<script setup lang="ts">
import Container from "@/components/ui/Container.vue";
import InstructionHeader from "@/features/experiment-core/components/InstructionHeader.vue";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { computed, inject, type Ref, ref } from "vue";
import ExperimentQuiz from "@/features/experiment-core/components/ExperimentQuiz.vue";
import { GraphExecutor } from "@/features/experiment-core";
import PuzzleSelector from "@/features/experiment-definitions/forced-choice/PuzzleSelector.vue";
import PuzzleRenderer from "@/components/PuzzleRenderer.vue";
import { Button } from "@/components/ui/button";

const executor = inject<Ref<GraphExecutor>>("experiment-executor");

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
      <PuzzleRenderer :definition="definition2" class="mx-auto" />
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
        <u><i>Left-click</i> to cycle between flag and safe mark placements.</u> You can right-click to place a safe
        mark directly.
      </li>
    </ul>

    <InstructionHeader>Your Task</InstructionHeader>
    <div class="flex flex-col gap-2">
      <p>
        There are <span class="font-bold">{{ executor?.total_trial_count }} trials</span> in this experiment.
        In each trial, you will be presented with a choice of two 3x3 minsweeper boards.
        Consider the two boards, and select the one you believe you can
        <span class="font-bold">solve the quickest.</span>
        Once you click the "Solve Selected Board" button, you will have to solve whichever board is currently selected.

      </p>

      <InstructionHeader></InstructionHeader>
      <div class="text-2xl text-center font-bold">Demo of Board Selection</div>
      <div class="text-center">Press your arrow key or click on a box to toggle between puzzles.</div>
      <div class="text-sm italic text-gray-500 text-center">
        You will have have up to 30 seconds to view puzzles and make a selection.
        <br />
        The timer will start after you first view a puzzle.
        <br />
      </div>

      <Container class="my-4 py-4 border-5 border-caution-tape">
        <PuzzleSelector :puzzles="[definition1, definition2]" @selection-changed="(_from_index, to_index) => selected_puzzle_index = to_index" />
        <div class="text-center">
          <Button :disabled="!can_proceed_to_solving" class="mt-5" variant="default"> Solve Selected Puzzle </Button>
        </div>
      </Container>
    </div>



    <InstructionHeader>Comprehension Quiz</InstructionHeader>
    <ExperimentQuiz :questions="quiz" @on-correct="$emit('complete')" />
  </Container>
</template>

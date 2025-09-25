<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { MinesweeperCell } from "@/services/game/engines/translator.ts";
import PuzzleMinesweeper from "@/features/games/minesweeper/minesweeper.puzzle.vue";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";

const PUZZLE_SCALE = 1.5;

// @ts-expect-error ignore any missing fields
const definition: PuzzleDefinition = { rows: 4, cols: 4 };

const boardPage1: Partial<PuzzleState> = {
  definition,
  board: [
    [MinesweeperCell.UNMARKED, MinesweeperCell.UNMARKED, 1, MinesweeperCell.EMPTY],
    [2, MinesweeperCell.UNMARKED, 1, MinesweeperCell.EMPTY],
    [2, 3, 2, 1],
    [MinesweeperCell.UNMARKED, MinesweeperCell.UNMARKED, MinesweeperCell.UNMARKED, MinesweeperCell.UNMARKED],
  ],
};

const boardPage2: Partial<PuzzleState> = {
  definition,
  board: [
    [MinesweeperCell.UNMARKED, MinesweeperCell.UNMARKED, 1, MinesweeperCell.EMPTY],
    [2, MinesweeperCell.UNMARKED_HIGHLIGHTED, 1, MinesweeperCell.EMPTY],
    [2, 3, 2, 1],
    [
      MinesweeperCell.UNMARKED_HIGHLIGHTED,
      MinesweeperCell.UNMARKED_HIGHLIGHTED,
      MinesweeperCell.UNMARKED_HIGHLIGHTED,
      MinesweeperCell.UNMARKED,
    ],
  ],
};

const boardPage3: Partial<PuzzleState> = {
  definition,
  board: [
    [MinesweeperCell.UNMARKED, MinesweeperCell.UNMARKED, 1, MinesweeperCell.EMPTY],
    [2, MinesweeperCell.UNMARKED, 1, MinesweeperCell.EMPTY],
    [2, 3, 2, 1],
    [MinesweeperCell.FLAG, MinesweeperCell.FLAG, MinesweeperCell.FLAG, MinesweeperCell.UNMARKED],
  ],
};

const boardSolved: Partial<PuzzleState> = {
  definition,
  board: [
    [MinesweeperCell.FLAG, MinesweeperCell.FLAG, 1, MinesweeperCell.EMPTY],
    [2, MinesweeperCell.SAFE, 1, MinesweeperCell.EMPTY],
    [2, 3, 2, 1],
    [MinesweeperCell.FLAG, MinesweeperCell.FLAG, MinesweeperCell.FLAG, MinesweeperCell.SAFE],
  ],
};

// Converting board1

// Converting board2
const board2: Partial<PuzzleState> = {
  // @ts-expect-error intentionally partially defined
  definition: {
    rows: 7,
    cols: 7,
  },
  board: [
    [1, 11, 1, 2, 11, 11, 1],
    [10, 11, 11, 10, 10, 10, 11],
    [1, 11, 11, 3, 5, 10, 11],
    [11, 11, 1, 2, 10, 3, 1],
    [11, 10, 11, 11, 10, 4, 11],
    [10, 2, 11, 11, 10, 10, 1],
    [1, 1, 11, 11, 2, 11, 11],
  ],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="4" slide-class="min-h-130">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Minesweeper is a logic puzzle played on a grid. Some squares are revealed and show numbers, while others
            remain unrevealed. Your goal is to identify
            <span class="font-bold">which unrevealed cells contain mines.</span>
          </div>
        </template>
        <template #board>
          <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="boardPage1" class="" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="flex flex-col gap-2">
            <div>
              Each <span class="font-bold">numbered cell</span> tells you how many mines are in its neighboring cells
              (horizontal, vertical, and diagonal).
            </div>
            <div>
              In the example below, the cell with a
              <span class="font-bold text-red-600">3</span> has four neighbors, three of which contain mines.
            </div>
          </div>
        </template>
        <template #board>
          <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="boardPage2" class="" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            You can flag <i class="md-cell md-cell-flag"></i> a cell to mark it as a suspected mine, or place a cross
            <i class="md-cell md-cell-empty"></i> to mark the cell as safe.
          </div>
          <div>
            In the example below, several flags have been placed to mark suspected mines, satisfying the number clues
            <span class="font-bold text-green-600">2</span>, <span class="font-bold text-red-600">3</span>,
            <span class="font-bold text-green-600">2</span>, and <span class="font-bold text-blue-600">1</span> in the
            second to last row:
          </div>
        </template>
        <template #board>
          <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="boardPage3" class="" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            A puzzle is solved when <span class="font-bold">all mines are flagged</span>, the remaining cells are
            unmarked or marked safe, and <span class="font-bold">all number clues are satisfied</span> (i.e., the number
            of adjacent flags matches the number on the clue cell).
          </div>
          <div>Below is an example of a solved board.</div>
        </template>
        <template #board>
          <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="boardSolved" class="" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #controls>
      <div>Left click on a cell to cycle between:</div>
      <ul class="list-decimal gap-2 h-full w-full ml-8">
        <li>Placing a flag <i class="md-cell md-cell-flag"></i></li>
        <li>Placing a safe mark <i class="md-cell md-cell-empty"></i></li>
        <li>Clearing the cell <i class="md-cell md-cell-unrevealed"></i></li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>

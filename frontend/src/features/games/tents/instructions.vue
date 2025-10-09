<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import type { PuzzleState, TentsMeta } from "@/services/game/engines/types.ts";
import PuzzleTents from "@/features/games/tents/tents.puzzle.vue";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";
import { TentsCell } from "@/services/game/engines/translator.ts";

const definition = {
  rows: 4,
  cols: 4,
  meta: {
    row_tent_counts: [2, 0, 1, 1],
    col_tent_counts: [1, 1, 1, 1],
  },
};

const boardPage1: PuzzleState<TentsMeta> = {
  // @ts-expect-error intentionally partially defined
  definition,
  board: [
    [0, 0, 0, 0],
    [1, 0, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 1, 0],
  ],
};

const boardPage2 = JSON.parse(JSON.stringify(boardPage1));
boardPage2.board[2][2] = TentsCell.TENT;
boardPage2.board[3][3] = TentsCell.TENT;

const boardPage3 = JSON.parse(JSON.stringify(boardPage1));
// boardPage3.board[0][0] = TentsCell.TENT;
boardPage3.board[0][2] = TentsCell.TENT;
boardPage3.board[2][2] = TentsCell.TENT;
// boardPage3.board[2][3] = TentsCell.TENT;
// boardPage3.board[3][1] = TentsCell.TENT;

const boardPage4 = JSON.parse(JSON.stringify(boardPage1));
boardPage4.board[0][0] = TentsCell.TENT;
boardPage4.board[0][2] = TentsCell.TENT;
boardPage4.board[2][2] = TentsCell.EMPTY;
boardPage4.board[2][3] = TentsCell.TENT;

const boardPage5 = JSON.parse(JSON.stringify(boardPage1));
boardPage5.board[0][0] = TentsCell.TENT;
boardPage5.board[0][2] = TentsCell.TENT;
boardPage5.board[3][1] = TentsCell.TENT;
boardPage5.board[2][3] = TentsCell.TENT;
for (let r = 0; r < boardPage5.board.length; r++) {
  for (let c = 0; c < boardPage5.board[r].length; c++) {
    const val = boardPage5.board[r][c];
    // skip trees (1) and tents
    if (val === TentsCell.TENT || val === 1) continue;
    boardPage5.board[r][c] = /* tent-free mark (green) */ (TentsCell as any).MARK ?? 3;
  }
}
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="5">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="mb-2">
            Tents is a logic puzzle in which the goal is to place tents
            <i class="md-cell md-cell-tent"></i> next to trees
            <i class="md-cell md-cell-tree"></i>
            subject to a number of constraints.
          </div>
          <div>
            Below is a 4x4 example board with 4 trees:
          </div>

        </template>
        <template #board>
          <PuzzleTents :state="boardPage1" :scale="1.2" class="mt-auto mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <p class="mx-auto">
            Each tree must be paired with exactly one tent, placed <span class="font-bold">horizontally or vertically adjacent.</span>
            A tree may have multiple tents next to it, but in the final solution only one of them forms its unique pair.
          </p>
          <br>
<!--          <div>-->
<!--            Multiple tents may be next to a tree (such as the middle tree in the second row),-->
<!--            <span class="font-bold">but only one of the trees will be paired with it</span>-->
<!--            in the final solution, ensuring a global 1-to-1, tree-to-tent pairing across the grid.-->
<!--          </div>-->
          <p>
            For example, the middle tree in the second row touches two tents, but each actually belongs to the tree below it.
          </p>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage3" :scale="1.2" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Tents must not touch each other, including diagonally. Once you place a tent, cells horizontally,
            vertically, and diagonally adjacent to it must be tent-free.
          </div>
          <br>
          <div>
            For instance, the configuration of tents below is <span class="font-bold">invalid</span> because the two
            tents touch each other diagonally:
          </div>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage2" :scale="1.2" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>The numbers on the edges indicate exactly how many tents are in that row or column.</div>
          <br>
          <ul class="list-disc ml-4">
            <li>
              For instance, the first row has a 2, requiring two tents, while the second row has 0, so it contains no
              tents.
            </li>
            <li>The first column has 1, so there will be exactly one tent in that column.</li>
          </ul>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage4" :scale="1.2" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page5>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <p>The game is solved when you’ve placed tents equal to the number of trees, following the rules above.</p>
          <br>
          <p>Below is an example of a solved board:</p>
          <br>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage5" :scale="1.2" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>



    <template #controls>
      <div>Left click to cycle forward, right click to cycle backward between:</div>
      <ul class="list-decimal ml-8">
        <li>Placing a tent <i class="md-cell md-cell-tent"></i></li>
        <li>Marking the cell as tent-free <i class="md-cell bg-green-300 rounded"></i></li>
        <li>Clearing the cell</li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>

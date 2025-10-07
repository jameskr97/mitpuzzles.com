<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import BoardBackground from "@/features/games.components/board.background.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { ref, watch } from "vue";
import { check_violation_rule } from "@/utils.ts";
import type { PuzzleState } from "@/services/game/engines/types.ts";
import { LightupCell } from "@/services/game/engines/translator.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleState;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

// Game Specific Logic
const LightWallStates = [
  LightupCell.WALL_0,
  LightupCell.WALL_1,
  LightupCell.WALL_2,
  LightupCell.WALL_3,
  LightupCell.WALL_4,
  LightupCell.WALL_NO_CONSTRAINT,
];
const lit = ref<boolean[]>([]);

function isCellLit(row: number, col: number): boolean {
  const i = row * props.state.definition.cols + col;
  return lit.value[i];
}

function update_lit_cells(board: number[][]) {
  // update lit cells when the board is modified
  // reset lit array to bulb locations (if a bulb is present, being lit is implied)
  for (let i = 0; i < lit.value.length; i++) lit.value[i] = false;

  // mark cardinal direction deltas
  const directions = [
    [-1, 0],
    [1, 0],
    [0, -1],
    [0, 1],
  ];

  for (let row = 0; row < props.state.definition.rows; row++) {
    for (let col = 0; col < props.state.definition.cols; col++) {
      if (board[row][col] !== LightupCell.BULB) continue; // skip if not a bulb

      for (const [dy, dx] of directions) {
        let r = row + dy;
        let c = col + dx;

        //A while we are in bounds and not hitting a wall
        while (r >= 0 && r < props.state.definition.rows && c >= 0 && c < props.state.definition.cols) {
          let i = r * props.state.definition.cols + c;
          if (LightWallStates.includes(board[r][c])) break;
          lit.value[i] = true;

          r += dy;
          c += dx;
        }
      }
    }
  }
}

watch(
  () => props.state.board,
  (board) => update_lit_cells(board),
  { deep: true, immediate: true },
);

const bind = props.interact?.getBridge();
const borderConfig = { outer: { thickness: 1, borderClass: "bg-black" } };
</script>

<template>
  <BoardContainer
    v-if="state"
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :scale="scale"
    :gap="1"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardBackground class="bg-black" />
    <BoardCells>
      <template v-slot:cell="{ row, col }">
        <div class="w-full h-full">
          <!-- Empty cells -->
          <div
            v-if="state.board[row][col] === LightupCell.EMPTY"
            class="bg-white bg-cover w-full h-full"
            :class="{
              'bg-white': !isCellLit(row, col) || state.board[row][col] === LightupCell.CROSS,
              'bg-yellow-200': isCellLit(row, col),
            }"
          ></div>

          <!-- Walls -->
          <div
            v-else-if="LightWallStates.includes(state.board[row][col])"
            class="bg-black h-full w-full flex items-center justify-center"
            :class="
              check_violation_rule(state.violations!, row, col, 'numbered_wall_constraint_violated')
                ? 'text-red-500'
                : 'text-white'
            "
          >
            {{ state.board[row][col] === LightupCell.WALL_NO_CONSTRAINT ? "" : state.board[row][col] }}
          </div>

          <!-- Bulbs -->
          <div
            v-else-if="state.board[row][col] === LightupCell.BULB"
            class="relative inset-0 h-full w-full flex items-center justify-center"
          >
            <div class="absolute grid bg-yellow-200 h-full w-full items-center justify-center"></div>

            <img
              :src="
                check_violation_rule(state.violations!, row, col, 'bulb_intersection_violation')
                  ? '/assets/lightup/bulb-violation.svg'
                  : '/assets/lightup/bulb.svg'
              "
              alt="Light Bulb"
              class="absolute w-full h-full rounded items-center justify-center"
            />
          </div>

          <!-- Cross -->
          <div
            v-else-if="state.board[row][col] === LightupCell.CROSS"
            class="flex justify-center items-center h-full w-full"
            :class="[ isCellLit(row, col) ? 'bg-yellow-200' : 'bg-white' ]"
          >
            <div
              class="bg-[url(/assets/lightup/cross.svg)] bg-contain w-8/12 h-8/12 bg-white"
              :class="[ isCellLit(row, col) ? 'bg-yellow-200' : 'bg-white' ]"
            ></div>
          </div>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>

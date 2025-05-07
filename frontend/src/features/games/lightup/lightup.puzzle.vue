<script setup lang="ts">
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import BoardBackground from "@/features/games/components/board.background.vue";
import { type Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/PuzzleModelBase";
import type { PuzzleStateLightup } from "@/services/states.ts";
import { LightupCellStates, LightWallStates } from "@/features/games/lightup/lightup.model.ts";

const props = defineProps<{
  scale?: number;
  state: Ref<any>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

function update_lit_cells(state: PuzzleStateLightup) {
  // reset lit array to bulb locations (if a bulb is present, being lit is implied)
  for (let i = 0; i < state.lit.length; i++) state.lit[i] = false;

  // mark cardinal direction deltas
  const directions = [
    [-1, 0],
    [1, 0],
    [0, -1],
    [0, 1],
  ];

  for (let row = 0; row < state.rows; row++) {
    for (let col = 0; col < state.cols; col++) {
      const i = row * state.cols + col;
      if (state.board[i] !== LightupCellStates.Bulb) continue; // skip if not a bulb

      for (const [dy, dx] of directions) {
        let r = row + dy;
        let c = col + dx;

        //A while we are in bounds and not hitting a wall
        while (r >= 0 && r < state.rows && c >= 0 && c < state.cols) {
          let i = r * state.cols + c;
          if (LightWallStates.includes(state.board[i])) break;
          if (state.board[i] === LightupCellStates.Bulb) break;
          state.lit[i] = true;

          r += dy;
          c += dx;
        }
      }
    }
  }
}

const m = createStateMachinePuzzleModel<PuzzleStateLightup>(
  props.state,
  LightupCellStates.NUM_STATES,
  (e, p) => emits("game-event", e, p),
  {
    allowedStates: [LightupCellStates.Empty, LightupCellStates.Bulb, LightupCellStates.Cross],
    canModifyCell(row: number, col: number, state: any) {
      return !LightWallStates.includes(state.board[row * state.cols + col]);
    },
    onCellClick(_row: number, _col: number, state: PuzzleStateLightup) {
      update_lit_cells(state);
    },
  },
);
const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
};
</script>

<template>
  <BoardContainer
    :rows="m.rows.value"
    :cols="m.cols.value"
    :scale="scale"
    :model="m"
    :gap="1"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction />
    <BoardBackground class="bg-black" />
    <BoardCells>
      <template v-slot:cell="{ row, col }">
        <div class="w-full h-full">
          <!-- Empty cells -->
          <div
            v-if="m.getCellState(row, col) === LightupCellStates.Empty"
            class="bg-white bg-cover w-full h-full"
          ></div>

          <!-- Walls -->
          <div
            v-else-if="LightWallStates.includes(m.getCellState(row, col))"
            class="bg-black h-full w-full flex items-center justify-center text-white"
          >
            {{ m.getCellState(row, col) === LightupCellStates.WallBlank ? "" : m.getCellState(row, col) }}
          </div>

          <!-- Bulbs -->
          <div
            v-else-if="m.getCellState(row, col) === LightupCellStates.Bulb"
            class="relative inset-0 h-full w-full flex items-center justify-center"
          >
            <div class="absolute grid bg-yellow-200 h-full w-full items-center justify-center"></div>

            <img
              src="/assets/lightup/bulb.svg"
              alt="Light Bulb"
              class="absolute w-full h-full rounded items-center justify-center"
            />
          </div>

          <!-- Cross -->
          <div
            v-else-if="m.getCellState(row, col) === LightupCellStates.Cross"
            :class="{ 'bg-yellow-200!': m.state.value.lit[m.index(row, col)] }"
            class="bg-[url(/assets/kakurasu/cross.svg)] bg-contain w-full h-full bg-white"
          ></div>
          <div v-else-if="m.state.value.lit[m.index(row, col)]" class="grid bg-yellow-200 h-full w-full text-sm"></div>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>

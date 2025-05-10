<script setup lang="ts">
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import { type Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/PuzzleModelBase.ts";
import type { PuzzleStateBattleship, PuzzleStateTents } from "@/services/states.ts";
import { PuzzleModelOps } from "@/features/games/composables/PuzzleModelOps.ts";
import { BattleshipCellStates } from "@/features/games/battleship/battleship.model.ts";

const props = defineProps<{
  scale?: number;
  state: Ref<any>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const m = createStateMachinePuzzleModel<PuzzleStateBattleship>(
  props.state,
  BattleshipCellStates.NUM_STATES,
  (e, p) => emits("game-event", e, p),
  {
    allowedStates: [
      BattleshipCellStates.Empty,
      BattleshipCellStates.Ship,
      BattleshipCellStates.Water,
    ],
    canModifyCell(row: number, col: number, state: PuzzleStateBattleship) {
      const cell =  Number(state.board_initial[row * state.cols + col])
      return cell !== BattleshipCellStates.Ship && cell !== BattleshipCellStates.Water;
    },
    onLeftGutterCellClick(row: number, _col: number, state: PuzzleStateTents) {
      PuzzleModelOps.changeLineState(true, row, state, BattleshipCellStates.Empty, BattleshipCellStates.Water);
    },
    onTopGutterCellClick(_row: number, col: number, state: PuzzleStateTents) {
      PuzzleModelOps.changeLineState(true, col, state, BattleshipCellStates.Empty, BattleshipCellStates.Water);

    },
  },
);

const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
};

/**
 * Returns Tailwind classes to remove rounding on sides where this ship cell
 * connects to another ship, creating a semi-circle effect.
 */
function getShipRoundedClasses(row: number, col: number): string[] {
  const isShip = (r: number, c: number) => m.getCellState(r, c) === BattleshipCellStates.Ship;

  // determine neighbors
  const neighbors: ("top" | "left" | "bottom" | "right")[] = [];
  if (isShip(row - 1, col)) neighbors.push("top");
  if (isShip(row, col - 1)) neighbors.push("left");
  if (isShip(row + 1, col)) neighbors.push("bottom");
  if (isShip(row, col + 1)) neighbors.push("right");

  if (neighbors.length === 0) return [];
  if (neighbors.length === 1) {
    switch (neighbors[0]) {
      case "top":
        return ["rounded-t-none"];
      case "left":
        return ["rounded-l-none"];
      case "bottom":
        return ["rounded-b-none"];
      case "right":
        return ["rounded-r-none"];
    }
  }
  return ["rounded-none"];
}
</script>

<template>
  <BoardContainer
    :rows="m.rows.value"
    :cols="m.cols.value"
    :gutter-top="1"
    :gutter-left="1"
    :scale="scale"
    :model="m"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction />
    <BoardCells>
      <template v-slot:cell="{ row, col }">
        <div class="w-full h-full flex items-center justify-center">
          <!-- water cell -->
          <div
            v-if="m.getCellState(row, col) === BattleshipCellStates.Water"
            class="w-full h-full bg-blue-300 flex items-center justify-center"
          >
            <!-- show dot if it's given in the board_initial -->
            <div
              v-if="Number(m.state.value.board_initial[row * m.cols.value + col]) === BattleshipCellStates.Ship"
              class="w-[2px] h-[2px] bg-white rounded-full z-10"
            ></div>
          </div>

          <!-- ship cell -->
          <div
            v-if="m.getCellState(row, col) === BattleshipCellStates.Ship"
            class="w-full h-full bg-blue-300 flex items-center justify-center"
          >
            <!-- show dot if it's given in the board_initial -->
            <div class="w-[8px] h-[8px] bg-black rounded-full" :class="getShipRoundedClasses(row, col)"></div>

            <div
              v-if="Number(m.state.value.board_initial[row * m.cols.value + col]) === BattleshipCellStates.Ship"
              class="absolute w-[2px] h-[2px] bg-white rounded-full z-10"
            ></div>
          </div>
        </div>
      </template>

      <template v-slot:top="{ col }">
        <div class="font-bold flex justify-center items-center h-full w-full">
          {{ m.state.value.col_counts[col] }}
        </div>
      </template>

      <template v-slot:left="{ row }">
        <div class="grid h-full font-bold text-end items-center justify-center">
          {{ m.state.value.row_counts[row] }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>

<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import type { BattleshipsMeta, PuzzleState } from "@/services/game/engines/types.ts";
import { BattleshipsCell } from "@/services/game/engines/translator.ts";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleState<BattleshipsMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
  inner: { thickness: 2, borderClass: "bg-black" },
};

/**
 * Returns Tailwind classes to remove rounding on sides where this ship cell
 * connects to another ship, creating a semi-circle effect.
 */
function getShipRoundedClasses(row: number, col: number): string[] {
  const isShip = (r: number, c: number) => {
    if (r >= props.state.definition.rows || r < 0) return false;
    if (c >= props.state.definition.cols || c < 0) return false;
    return props.state.board[r][c] === BattleshipsCell.SHIP;
  }

  // determine neighbors
  const neighbors: ("top" | "left" | "bottom" | "right")[] = [];
  if (isShip(row - 1, col)) neighbors.push("top");
  if (isShip(row, col - 1)) neighbors.push("left");
  if (isShip(row + 1, col)) neighbors.push("bottom");
  if (isShip(row, col + 1)) neighbors.push("right");

  if (row === 2 && col == 0){
    console.log(props.state.board)
    console.log(`(${row}, ${col}) has ${neighbors.length} neighbors.`)
  }

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

const bind = props.interact?.getBridge();
</script>

<template>
  <BoardContainer
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :gutter-top="1"
    :gutter-left="1"
    :scale="scale"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardCells>
      <template v-slot:cell="{ row, col }">
        <div class="w-full h-full flex items-center justify-center">
          <!-- water cell -->
          <div v-if="state.board[row][col] === BattleshipsCell.WATER" class="w-full h-full bg-blue-300 flex items-center justify-center">
            <!-- show dot if it's given in the board_initial -->
            <div v-if="state.definition.initial_state[row][col] === BattleshipsCell.SHIP"
              class="w-[2px] h-[2px] bg-white rounded-full z-10 text-red-500"
            >{{state.definition.initial_state[row][col]}}</div>
          </div>

          <!-- ship cell -->
          <div v-if="state.board[row][col]  === BattleshipsCell.SHIP" class="w-full h-full bg-blue-300 flex items-center justify-center">
            <!-- show dot if it's given in the board_initial -->
            <div class="w-11/12 h-11/12 bg-black rounded-full" :class="getShipRoundedClasses(row, col)"></div>

            <div
              v-if="state.definition.initial_state[row][col] === BattleshipsCell.SHIP"
              class="absolute w-[2px] h-[2px] bg-white rounded-full z-10"
            ></div>
          </div>
        </div>
      </template>

      <template v-slot:top="{ col }">
        <div class="font-bold flex justify-center items-center h-full w-full">
          {{ state.definition.meta.col_sums[col] }}
        </div>
      </template>

      <template v-slot:left="{ row }">
        <div class="grid h-full font-bold text-end items-center justify-center">
          {{ state.definition.meta.row_sums[row] }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>

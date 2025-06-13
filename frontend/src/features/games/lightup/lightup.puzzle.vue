<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import BoardBackground from "@/features/games.components/board.background.vue";
import type { PuzzleStateLightup } from "@/services/states.ts";
import { LightupCellStates, LightWallStates } from "@/features/games/lightup/lightup.model.ts";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { onMounted, ref, watch } from "vue";
import { check_violation_rule } from "@/utils.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleStateLightup;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

// Game Specific Logic
const lit = ref<boolean[]>([]);
function isCellLit(row: number, col: number): boolean {
  const i = row * props.state.cols + col;
  return lit.value[i];
}
function update_lit_cells(board: number[]) {
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

  for (let row = 0; row < props.state.rows; row++) {
    for (let col = 0; col < props.state.cols; col++) {
      const i = row * props.state.cols + col;
      if (board[i] !== LightupCellStates.Bulb) continue; // skip if not a bulb

      for (const [dy, dx] of directions) {
        let r = row + dy;
        let c = col + dx;

        //A while we are in bounds and not hitting a wall
        while (r >= 0 && r < props.state.rows && c >= 0 && c < props.state.cols) {
          let i = r * props.state.cols + c;
          if (LightWallStates.includes(board[i])) break;
          lit.value[i] = true;

          r += dy;
          c += dx;
        }
      }
    }
  }
}

props.interact?.addGameBehaviour((_) => ({
  onBoardModified: (board: number[]) => update_lit_cells(board),
}));

if (!props.interact) {
  watch(
    () => props.state.board,
    (board) => {
      update_lit_cells(board);
    },
  );
}

const bind = props.interact?.getBridge();
const borderConfig = { outer: { thickness: 1, borderClass: "bg-black" } };
onMounted(() => update_lit_cells(props.state.board));
</script>

<template>
  <BoardContainer :rows="state.rows" :cols="state.cols" :scale="scale" :gap="1" :border-config="borderConfig">
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardBackground class="bg-black" />
    <BoardCells>
      <template v-slot:cell="{ row, col }">
        <div class="w-full h-full">
          <!-- Empty cells -->
          <div
            v-if="state.board[row * state.cols + col] === LightupCellStates.Empty"
            class="bg-white bg-cover w-full h-full"
            :class="{
              'bg-white': !isCellLit(row, col),
              'bg-yellow-200': isCellLit(row, col),
            }"
          ></div>

          <!-- Walls -->
          <div
            v-else-if="LightWallStates.includes(state.board[row * state.cols + col])"
            class="bg-black h-full w-full flex items-center justify-center"
            :class="
              check_violation_rule(state.violations!, row, col, 'numbered_wall_constraint_violated')
                ? 'text-red-500'
                : 'text-white'
            "
          >
            {{
              state.board[row * state.cols + col] === LightupCellStates.WallBlank
                ? ""
                : state.board[row * state.cols + col]
            }}
          </div>

          <!-- Bulbs -->
          <div
            v-else-if="state.board[row * state.cols + col] === LightupCellStates.Bulb"
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
            v-else-if="state.board[row * state.cols + col] === LightupCellStates.Cross"
            class="bg-[url(/assets/kakurasu/cross.svg)] bg-contain w-full h-full bg-white"
            :class="{
              'bg-yellow-200': isCellLit(row, col),
            }"
          ></div>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>

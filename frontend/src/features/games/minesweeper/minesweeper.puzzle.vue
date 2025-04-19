<script setup lang="ts">
import { type MinesweeperState, ModelMinesweeperPuzzle } from "@/features/games/minesweeper/minesweeper.model";
import GameGrid from "@/components/game/game.grid.vue";
import { reactive, type Ref } from "vue";

const props = defineProps<{
  scale?: number;
  state: Ref<MinesweeperState>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const model = reactive<ModelMinesweeperPuzzle>(
  new ModelMinesweeperPuzzle(props.state.value, (event: string, payload: object) => {
    emits("game-event", event, payload);
  }),
);
</script>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :scale="scale"
    :gap="0"
    @grid-leave="model.onGridLeave()"
    @mouse-down="model.onCellMouseDown($event.row, $event.col)"
    @mouse-up="model.onCellMouseUp($event.row, $event.col)"
    @cell-enter="model.onCellMouseEnter($event.row, $event.col)"
    @cell-leave="model.onCellMouseLeave($event.row, $event.col)"
  >
    <!-- prettier-ignore -->
    <template v-slot:cell="props">
      <div class="w-full h-full select-none bg-[url(/assets/minesweeper/cell-empty.svg)]">
        <img v-if="model.getCellNumber(props.row, props.col) === 1" src="/assets/minesweeper/number-1.svg" alt="1" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 2" src="/assets/minesweeper/number-2.svg" alt="2" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 3" src="/assets/minesweeper/number-3.svg" alt="3" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 4" src="/assets/minesweeper/number-4.svg" alt="4" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 5" src="/assets/minesweeper/number-5.svg" alt="5" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 6" src="/assets/minesweeper/number-6.svg" alt="6" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 7" src="/assets/minesweeper/number-7.svg" alt="7" class="bg-auto w-full h-full" draggable="false" />
        <img v-if="model.getCellNumber(props.row, props.col) === 8" src="/assets/minesweeper/number-8.svg" alt="8" class="bg-auto w-full h-full" draggable="false" />

        <img v-if="model.isCellUnmarked(props.row, props.col)" src="/assets/minesweeper/unopened-square.svg" alt="Unmarked" class="w-full h-full" />
        <img v-if="model.isCellFlagged(props.row, props.col)" src="/assets/minesweeper/flag.svg" alt="Flagged" class="w-full h-full bg-[url(/assets/minesweeper/unopened-square.svg)]" />
        <img v-if="model.isCellSafe(props.row, props.col)" src="/assets/minesweeper/cell-safe.svg" alt="Safe" class="w-full h-full bg-[url(/assets/minesweeper/unopened-square.svg)]" />
        <img v-if="model.isCellInDangerZone(props.row, props.col)" src="/assets/minesweeper/cell-empty.svg" alt="Danger Zone" class="w-full h-full" />
      </div>
    </template>
  </GameGrid>
</template>

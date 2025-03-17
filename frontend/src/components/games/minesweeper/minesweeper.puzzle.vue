<script setup lang="ts">
import { ModelMinesweeperPuzzle } from "@/components/games/minesweeper/minesweeper.model";
import GameGrid from "@/components/ui/game/game.grid.vue";
import { reactive } from "vue";

////////////////////////////////////////////////////////////////////////////////
// Props + Events
defineProps<{
  scale?: number;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const model = reactive<ModelMinesweeperPuzzle>(
  new ModelMinesweeperPuzzle((event: string, payload: object) => {
    emits("game-event", event, payload);
  })
);
</script>

<template>
  <!-- Grid container for the game board itself -->
  <div class="flex flex-row gap-10">
    <GameGrid
      :rows="model.ROWS"
      :cols="model.COLS"
      :size="scale"
      class="rounded border-1 border-[#757575] bg-[#757575]"
      cell-class="bg-[url(/assets/minesweeper/cell-empty.svg)]"
      @grid-leave="() => model.onGridLeave()"
      @mouse-down="model.onCellMouseDown($event.row, $event.col)"
      @mouse-up="model.onCellMouseUp($event.row, $event.col)"
      @cell-enter="model.onCellMouseEnter($event.row, $event.col)"
      @cell-leave="model.onCellMouseLeave($event.row, $event.col)"
    >
      <!-- prettier-ignore -->
      <template v-slot:cell="props">
        <!-- Number Specific Background Options -->
        <img v-if="model.getCellNumber(props.row, props.col) === 1" src="/assets/minesweeper/number-1.svg" alt="1" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 2" src="/assets/minesweeper/number-2.svg" alt="2" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 3" src="/assets/minesweeper/number-3.svg" alt="3" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 4" src="/assets/minesweeper/number-4.svg" alt="4" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 5" src="/assets/minesweeper/number-5.svg" alt="5" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 6" src="/assets/minesweeper/number-6.svg" alt="6" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 7" src="/assets/minesweeper/number-7.svg" alt="7" class="w-full h-full rounded-sm" />
        <img v-if="model.getCellNumber(props.row, props.col) === 8" src="/assets/minesweeper/number-8.svg" alt="8" class="w-full h-full rounded-sm" />

        <!-- State Specific Background Options -->
        <img v-if="model.isCellUnmarked(props.row, props.col)" src="/assets/minesweeper/unopened-square.svg" alt="Unmarked" class="w-full h-full rounded-sm" />
        <img v-if="model.isCellFlagged(props.row, props.col)" src="/assets/minesweeper/flag.svg" alt="Flagged" class="w-full h-full rounded-sm" />
        <img v-if="model.isCellSafe(props.row, props.col)" src="/assets/minesweeper/cell-safe.svg" alt="Safe" class="w-full h-full rounded-sm" />
        <img v-if="model.isCellInDangerZone(props.row, props.col)" src="/assets/minesweeper/cell-empty.svg" alt="Danger Zone" class="w-full h-full rounded-sm" />
      </template>
    </GameGrid>
  </div>
</template>

<script setup lang="ts">
import type { PuzzleMinesweeper } from "@/api/app";
import { ModelMinesweeperPuzzle } from "@/components/games/minesweeper/minesweeper.model";
import GameGrid from "@/components/ui/game/game.grid.vue";
import type { useMinesweeperStore } from "@/store/game";
import { reactive } from "vue";

////////////////////////////////////////////////////////////////////////////////
// Props + Events
const props = withDefaults(
  defineProps<{
    store: ReturnType<typeof useMinesweeperStore>;
    puzzle: PuzzleMinesweeper;
    scale?: number;
  }>(),
  { scale: 2 }
);
const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const model = reactive<ModelMinesweeperPuzzle>(
  new ModelMinesweeperPuzzle(props.store, (event: string, payload: object) => {
    emits("game-event", event, payload);
  })
);
</script>

<template>
  <!-- Grid container for the game board itself -->
  <div class="flex flex-row gap-10">
    <GameGrid
      :rows="store.puzzle.rows"
      :cols="store.puzzle.cols"
      :size="scale"
      class="rounded border-1 border-[#757575] bg-[#757575]"
      @grid-leave="() => model.onGridLeave()"
      @mouse-down="model.onCellMouseDown($event.row, $event.col)"
      @mouse-up="model.onCellMouseUp($event.row, $event.col)"
      @cell-enter="model.onCellMouseEnter($event.row, $event.col)"
      @cell-leave="model.onCellMouseLeave($event.row, $event.col)"
    >
      <!-- prettier-ignore -->
      <template v-slot:cell="props">
        <!-- Number Specific Background Options -->
        <div v-if="model.getCellNumber(props.row, props.col) === 1"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-1.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 2"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-2.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 3"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-3.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 4"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-4.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 5"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-5.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 6"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-6.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 7"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-7.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.getCellNumber(props.row, props.col) === 8"  class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/number-8.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>

        <!-- State Specific Background Options -->
        <div v-if="model.isCellUnmarked(props.row, props.col)"       class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/unopened-square.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.isCellFlagged(props.row, props.col)"        class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/flag.svg),_url(/assets/minesweeper/unopened-square.svg)]"></div>
        <div v-if="model.isCellSafe(props.row, props.col)"           class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/cell-safe.svg),_url(/assets/minesweeper/cell-empty.svg)]"></div>
        <div v-if="model.isCellInDangerZone(props.row, props.col)"   class="w-full h-full rounded-sm bg-[url(/assets/minesweeper/cell-empty.svg)]"></div>
      </template>
    </GameGrid>
  </div>
</template>
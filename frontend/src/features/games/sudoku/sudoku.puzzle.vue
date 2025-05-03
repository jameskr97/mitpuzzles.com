<script setup lang="ts">
import GameGrid from "@/components/game/game.grid.vue";
import { createSudokuPuzzleModel } from "@/features/games/composables/puzzleModelBase.ts";

const props = defineProps<{
  scale?: number;
  state: any;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const m = createSudokuPuzzleModel(props.state);
</script>

<template>
  <GameGrid :rows="m.rows.value" :cols="m.cols.value" :scale="scale" :cell-size="7" :model="m">
    <template v-slot:cell="{ row, col }">
      <div
        class="flex justify-center items-center h-full w-full"
        :class="{
          'border-red-500 border-[0.5px]': m.isCellActive(row, col),
          'bg-slate-300': m.highlight.shouldHighlightCell(row, col),
          'text-blue-600': m.canModifyCell(row, col),
        }"
      >
        {{ m.getCellValue(row, col) }}
      </div>
    </template>
  </GameGrid>
</template>

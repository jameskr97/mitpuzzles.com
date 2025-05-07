<script setup lang="ts">
import { createSudokuPuzzleModel } from "@/features/games/composables/PuzzleModelBase.ts";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import { computed } from "vue";

const props = defineProps<{ scale?: number; state: any }>();
const m = createSudokuPuzzleModel(props.state);

const borderConfig = computed(() => ({
  everyNthCol: { n: Math.sqrt(m.cols.value), style: { thickness: 2 } },
  everyNthRow: { n: Math.sqrt(m.rows.value), style: { thickness: 2 } },
  outer: { thickness: 2, borderClass: "bg-black" },
}));

defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();
</script>

<template>
  <BoardContainer :model="m" :cols="m.cols.value" :rows="m.rows.value" :scale="scale" :border-config="borderConfig">
    <BoardBorders />
    <BoardInteraction />
    <BoardCells>
      <template #cell="{ row, col }">
        <div
          class="flex justify-center items-center h-full w-full"
          :class="{
            'border-blue-500 border-[0.5px]': m.isCellActive(row, col),
            'bg-slate-300': m.highlight.shouldHighlightCell(row, col),
            'text-blue-600': m.canModifyCell(row, col),
          }"
        >
          {{ m.getCellValue(row, col) }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>

  <!--    <GameGrid :rows="m.rows.value" :cols="m.cols.value" :scale="scale" :cell-size="7" :model="m">-->
  <!--      <template v-slot:cell="{ row, col }">-->
  <!--        <div-->
  <!--          class="flex justify-center items-center h-full w-full"-->
  <!--          :class="{-->
  <!--            'border-red-500 border-[0.5px]': m.isCellActive(row, col),-->
  <!--            'bg-slate-300': m.highlight.shouldHighlightCell(row, col),-->
  <!--            'text-blue-600': m.canModifyCell(row, col),-->
  <!--          }"-->
  <!--        >-->
  <!--          {{ m.getCellValue(row, col) }}-->
  <!--        </div>-->
  <!--      </template>-->
  <!--    </GameGrid>-->
</template>

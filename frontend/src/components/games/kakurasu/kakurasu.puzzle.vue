<script setup lang="ts">
import { KakurasuCellStates, ModelKakurasuPuzzle } from '@/components/games/kakurasu/kakurasu.model';
import GameGrid from '@/components/ui/game/game.grid.vue';
defineProps({
  scale: { type: Number, required: false, default: 1 },
});

const model = new ModelKakurasuPuzzle();
</script>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :size="scale"
    grid-class="border-5"
    cell-style="border-1"
    @mouse-up="model.onCellClick($event.row, $event.col, $event.input_event)"
  >
    <template v-slot:cell="{ row, col }">
        <div v-if="model.getCellState(row, col) === KakurasuCellStates.Filled" class="h-full flex items-center justify-center">
            <div class="bg-black h-11/12 w-11/12"></div>
        </div>

        <div v-if="model.getCellState(row, col) === KakurasuCellStates.Crossed" class="h-full flex items-center justify-center">
            <div class="bg-[url(/assets/kakurasu/cross.svg)] bg-contain h-[50%] w-[50%]"></div>
        </div>
    </template>

    <template v-slot:top="{ col, size }">
        <span
            :style="{ fontSize: size / 2 + 'rem' }"
            class="h-full text-gray-500 grid place-items-center align-middle"
        >{{ col + 1 }}</span>
    </template>

    <template v-slot:left="{ row, size }">
        <span
            :style="{ fontSize: size / 2 + 'rem' }"
            class="h-full text-gray-500 grid place-items-center align-middle"
        >{{ row + 1 }}</span>
    </template>

    <template v-slot:bottom="{ col, size }">
        <span
            :style="{ fontSize: size + 'rem' }"
            class="h-full grid place-items-center align-middle"
        >{{ model.hintCol[col] }}</span>
    </template>

    <template v-slot:right="{ row, size }">
        <span
            :style="{ fontSize: size + 'rem' }"
            class="h-full grid place-items-center align-middle"
        >{{ model.hintRow[row] }}</span>
    </template>
  </GameGrid>
</template>

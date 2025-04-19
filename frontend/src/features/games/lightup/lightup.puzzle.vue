<script setup lang="ts">
import GameGrid from "@/components/game/game.grid.vue";
import { ModelLightupPuzzle } from "@/features/games/lightup/lightup.model";
import { reactive, type Ref } from "vue";

const props = defineProps<{
  scale?: number;
  state: Ref<any>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const model = reactive(
  new ModelLightupPuzzle(props.state.value, (event: string, payload: object) => {
    emits("game-event", event, payload);
  }),
);
</script>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :scale="scale"
    @cell-click="model.onCellClick($event.row, $event.col)"
  >
    <template v-slot:cell="{ row, col }">
      <div class="w-full h-full">
        <div v-if="model.isWall(row, col)" class="bg-black h-full w-full flex items-center justify-center text-white">
          {{ model.getWallNumber(row, col) }}
        </div>

        <div v-if="model.isBulb(row, col)" class="relative inset-0 h-full w-full flex items-center justify-center">
          <div class="absolute grid bg-yellow-200 h-full w-full items-center justify-center"></div>

          <img
            src="/assets/lightup/bulb.svg"
            alt="Light Bulb"
            class="absolute w-full h-full rounded items-center justify-center"
          />
        </div>

        <div v-if="model.isLit(row, col)" class="grid bg-yellow-200 h-full w-full text-sm"></div>
      </div>
    </template>
  </GameGrid>
</template>

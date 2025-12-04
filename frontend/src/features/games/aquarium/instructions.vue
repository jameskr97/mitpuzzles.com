<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
import type { PuzzleDefinition, PuzzleState } from "@/core/games/types/puzzle-types.ts";
import  { AquariumCell, type AquariumMeta } from "@/features/games/aquarium/useAquariumGame.ts";
import AquariumCanvas from "@/features/games/aquarium/AquariumCanvas.vue";


const def: PuzzleDefinition<AquariumMeta> = {
  puzzle_type: "aquarium",
  rows: 6,
  cols: 6,
  initial_state: [
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
  ],
  meta: {
    row_hints: [5, 4, 4, 1, 5, 5],
    col_hints: [4, 5, 5, 5, 4, 1],
    regions: [
      [1, 2, 2, 2, 2, 2],
      [1, 3, 4, 4, 5, 5],
      [1, 3, 8, 5, 5, 6],
      [9, 9, 8, 7, 7, 6],
      [9, 9, 8, 8, 7, 6],
      [9, 9, 9, 8, 7, 6],
    ],
  }
};

const page1: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1]
  ],
}

const page2left: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-3, -1, -1, -1, -1, -1],
    [-3, -1, -1, -1, -3, -3],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1]
  ],
}

const page2right: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -3, -1, -1, -1],
    [-1, -1, -3, -3, -1, -1],
    [-1, -1, -1, -3, -1, -1]
  ],
}

const page3: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-3, -1, -1, -1, -1, -1],
    [-3, -3, -1, -1, -1, -1],
    [-3, -3, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1]
  ],
}

const page4left: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-3, -3, -3, -3, -1, -3]
  ],
}

const page4right: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [-3, -3, -3, -1, -3, -3]
  ],
}

const page5: PuzzleState<AquariumMeta> = {
  definition: def,
  board: [
    [-1, -3, -3, -3, -3, -3],
    [-3, -3, -3, -3, -1, -1],
    [-3, -3, -1, -3, -3, -1],
    [-1, -1, -3, -1, -1, -1],
    [-3, -3, -3, -3, -3, -1],
    [-3, -3, -3, -3, -3, -1]
  ],
}
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:aquarium:intro')"></div>
          <div v-html="$t('puzzle:aquarium:goal')"></div>
          <div v-html="$t('puzzle:aquarium:board_example')"></div>
        </template>
        <template #board>
          <AquariumCanvas :state="page1" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage :board_columns="2" board_max_width="max-w-100">
        <template #instruction>
          <div v-html="$t('puzzle:aquarium:rule_gravity')"></div>
          <div v-html="$t('puzzle:aquarium:rule_gravity_invalid')"></div>
          <div v-html="$t('puzzle:aquarium:rule_gravity_valid')"></div>
        </template>
        <template #board>
          <div class="flex flex-col gap-2 text-center">
            <AquariumCanvas :state="page2left" class="-translate-x-3" />
            <div class="text-red-500">Incorrect Placement</div>
          </div>
          <div class="flex flex-col gap-2 text-center">
            <AquariumCanvas :state="page2right" class="-translate-x-3" />
            <div class="text-green-500">Correct Placement</div>
          </div>
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:aquarium:rule_independent')"></div>
          <div v-html="$t('puzzle:aquarium:rule_independent_example')"></div>
        </template>
        <template #board>
          <AquariumCanvas :state="page3" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage :board_columns="2" board_max_width="max-w-100">
        <template #instruction>
          <div v-html="$t('puzzle:aquarium:rule_hints')"></div>
          <div v-html="$t('puzzle:aquarium:rule_hints_example')"></div>
        </template>
        <template #board>
          <div class="flex flex-col gap-2 text-center">
            <AquariumCanvas :state="page4left" class="-translate-x-3" />
          </div>
          <div class="flex flex-col gap-2 text-center">
            <AquariumCanvas :state="page4right" class="-translate-x-3" />
          </div>
        </template>
      </InstructionPage>
    </template>

    <template #page5>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:aquarium:solved')"></div>
          <div v-html="$t('puzzle:aquarium:solved_board')"></div>
        </template>
        <template #board>
          <AquariumCanvas :state="page5" />
        </template>
      </InstructionPage>
    </template>


    <template #controls>
      <div>{{ $t('puzzle:aquarium:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:aquarium:control_water')"></li>
        <li v-html="$t('puzzle:aquarium:control_cross')"></li>
        <li v-html="$t('puzzle:aquarium:control_clear')"></li>
      </ul>
    </template>
  </InstructionSlider>
</template>

<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:minesweeper:intro')"></div>
          <div class="text-lg font-semibold">{{ $t('puzzle:minesweeper:board_example') }}</div>
        </template>
        <template #board>
          <img src="/assets/instructions/minesweeper.page1.png" alt="Minesweeper board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:minesweeper:rule_numbered')"></div>
          <div v-html="$t('puzzle:minesweeper:example_numbered')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/minesweeper.page2.png" alt="Minesweeper numbered cells" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:minesweeper:control_flag_safe')"></div>
          <div v-html="$t('puzzle:minesweeper:example_flags')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/minesweeper.page3.png" alt="Minesweeper flags" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:minesweeper:solved')"></div>
          <div>{{ $t('puzzle:minesweeper:solved_board') }}</div>
        </template>
        <template #board>
          <img src="/assets/instructions/minesweeper.page4.png" alt="Minesweeper solved" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:minesweeper:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:minesweeper:control_place_flag')"></li>
        <li v-html="$t('puzzle:minesweeper:control_place_safe')"></li>
        <li v-html="$t('puzzle:minesweeper:control_clear')"></li>
      </ul>
    </template>
  </InstructionSlider>
</template>

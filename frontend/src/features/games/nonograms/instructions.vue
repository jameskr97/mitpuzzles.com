<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:nonograms:intro')"></p>
          <p>{{ $t('puzzle:nonograms:board_example') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/nonograms.page1.png" alt="Nonograms board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:nonograms:rule_hints')"></p>
          <p v-html="$t('puzzle:nonograms:goal')"></p>
        </template>
        <template #board>
          <img src="/assets/instructions/nonograms.page2.png" alt="Nonograms rules" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage :board_columns="2" board_max_width="max-w-100">
        <template #instruction>
          <p>{{ $t('puzzle:nonograms:example_column') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/nonograms.page3left.png" alt="Nonograms column example 1" />
          <img src="/assets/instructions/nonograms.page3right.png" alt="Nonograms column example 2" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage :board_columns="2" board_max_width="max-w-100">
        <template #instruction>
          <div>{{ $t('puzzle:nonograms:example_row') }}</div>
          <div v-html="$t('puzzle:nonograms:rule_multiple_runs')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/nonograms.page4left.png" alt="Nonograms row example 1" />
          <img src="/assets/instructions/nonograms.page4right.png" alt="Nonograms row example 2" />
        </template>
      </InstructionPage>
    </template>

    <template #page5>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:nonograms:solved') }}</p>
          <p>{{ $t('puzzle:nonograms:solved_board') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/nonograms.page5.png" alt="Nonograms solved" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:nonograms:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:nonograms:control_place_box')"></li>
        <li v-html="$t('puzzle:nonograms:control_place_cross')"></li>
        <li>{{ $t('puzzle:nonograms:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

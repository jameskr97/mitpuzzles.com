<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <p class="mb-2" v-html="$t('puzzle:kakurasu:intro')"></p>
          <p class="mb-2" v-html="$t('puzzle:kakurasu:weights_explanation')"></p>
          <p v-html="$t('puzzle:kakurasu:board_example')"></p>
        </template>
        <template #board>
          <img src="/assets/instructions/kakurasu.page1and2.png" alt="Kakurasu board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:kakurasu:rule_row_sum')"></div>
          <div v-html="$t('puzzle:kakurasu:rule_col_sum')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/kakurasu.page1and2.png" alt="Kakurasu rules" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage :board_columns="2" board_max_width="max-w-100">
        <template #instruction>
          <div v-html="$t('puzzle:kakurasu:goal')"></div>
          <div v-html="$t('puzzle:kakurasu:multiple_solutions_note')"></div>
          <div v-html="$t('puzzle:kakurasu:example_row')"></div>
        </template>
        <template #board>
          <div class="flex flex-col gap-2 text-center">
            <img src="/assets/instructions/kakurasu.page3left.png" alt="Kakurasu row example 1" />
            <div>{{ $t('puzzle:kakurasu:example_row_calc1') }}</div>
          </div>
          <div class="flex flex-col gap-2 text-center">
            <img src="/assets/instructions/kakurasu.page3right.png" alt="Kakurasu row example 2" />
            <div>{{ $t('puzzle:kakurasu:example_row_calc2') }}</div>
          </div>
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage :board_columns="2" board_max_width="max-w-100">
        <template #instruction>
          <div v-html="$t('puzzle:kakurasu:example_col')"></div>
        </template>
        <template #board>
          <div class="flex flex-col gap-2 text-center">
            <img src="/assets/instructions/kakurasu.page4left.png" alt="Kakurasu column example 1" />
            <div>{{ $t('puzzle:kakurasu:example_col_calc1') }}</div>
          </div>
          <div class="flex flex-col gap-2 text-center">
            <img src="/assets/instructions/kakurasu.page4right.png" alt="Kakurasu column example 2" />
            <div>{{ $t('puzzle:kakurasu:example_col_calc2') }}</div>
          </div>
        </template>
      </InstructionPage>
    </template>

    <template #page5>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:kakurasu:solved')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/kakurasu.page5.png" alt="Kakurasu solved" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:kakurasu:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:kakurasu:control_place_box')"></li>
        <li v-html="$t('puzzle:kakurasu:control_place_cross')"></li>
        <li>{{ $t('puzzle:kakurasu:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

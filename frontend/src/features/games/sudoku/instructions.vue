<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:intro')"></div>
          <div v-html="$t('puzzle:sudoku:goal')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/sudoku.page1.png" alt="Sudoku board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:rule_row')"></div>
          <div class="italic" v-html="$t('puzzle:sudoku:rule_row_example')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/sudoku.page2.png" alt="Sudoku row rule" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:rule_col')"></div>
          <div class="italic" v-html="$t('puzzle:sudoku:rule_col_example')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/sudoku.page3.png" alt="Sudoku column rule" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:rule_box')"></div>
          <div class="italic" v-html="$t('puzzle:sudoku:rule_box_example')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/sudoku.page4.png" alt="Sudoku box rule" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <ul class="list-disc ml-4">
        <li v-html="$t('puzzle:sudoku:control_select')"></li>
        <li v-html="$t('puzzle:sudoku:control_input')"></li>
      </ul>
    </template>
  </InstructionSlider>
</template>

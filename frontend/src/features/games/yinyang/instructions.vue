<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:yinyang:intro')"></p>
          <p>{{ $t('puzzle:yinyang:board_example') }}</p>
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:yinyang:rule_connected') }}</p>
          <p>{{ $t('puzzle:yinyang:rule_no_2x2') }}</p>
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:yinyang:rule_clues') }}</p>
          <p>{{ $t('puzzle:yinyang:solved') }}</p>
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:yinyang:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:yinyang:control_mark_black')"></li>
        <li v-html="$t('puzzle:yinyang:control_mark_white')"></li>
        <li>{{ $t('puzzle:yinyang:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

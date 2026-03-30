<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:norinori:intro')"></p>
          <p v-html="$t('puzzle:norinori:goal')"></p>
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:norinori:rule_two_per_region')"></p>
          <p v-html="$t('puzzle:norinori:rule_domino')"></p>
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:norinori:rule_cross_region')"></p>
          <p>{{ $t('puzzle:norinori:solved') }}</p>
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:norinori:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li>{{ $t('puzzle:norinori:control_shade') }}</li>
        <li>{{ $t('puzzle:norinori:control_cross') }}</li>
        <li>{{ $t('puzzle:norinori:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

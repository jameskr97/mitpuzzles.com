<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:tents:intro')"></div>
          <div>{{ $t('puzzle:tents:board_example') }}</div>
        </template>
        <template #board>
          <img src="/assets/instructions/tents.page1.png" alt="Tents board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:tents:rule_pairing')"></p>
          <p>{{ $t('puzzle:tents:example_pairing') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/tents.page2.png" alt="Tents pairing" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <div>{{ $t('puzzle:tents:rule_no_touch') }}</div>
          <div v-html="$t('puzzle:tents:example_invalid')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/tents.page3.png" alt="Tents no touch rule" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage>
        <template #instruction>
          <div>{{ $t('puzzle:tents:rule_counts') }}</div>
          <ul class="list-disc ml-4">
            <li>{{ $t('puzzle:tents:example_row') }}</li>
            <li>{{ $t('puzzle:tents:example_col') }}</li>
          </ul>
        </template>
        <template #board>
          <img src="/assets/instructions/tents.page4.png" alt="Tents counts" />
        </template>
      </InstructionPage>
    </template>

    <template #page5>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:tents:solved') }}</p>
          <p>{{ $t('puzzle:tents:solved_board') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/tents.page5.png" alt="Tents solved" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:tents:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:tents:control_place_tent')"></li>
        <li v-html="$t('puzzle:tents:control_mark_free')"></li>
        <li>{{ $t('puzzle:tents:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:mosaic:intro')"></p>
          <p>{{ $t('puzzle:mosaic:board_example') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/mosaic.page1and2.png" alt="Mosaic board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:mosaic:rule_adjacent')"></p>
          <p>{{ $t('puzzle:mosaic:example_adjacent') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/mosaic.page1and2.png" alt="Mosaic rules" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:mosaic:control_mark') }}</p>
          <p>{{ $t('puzzle:mosaic:example_marked') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/mosaic.page3.png" alt="Mosaic marked cells" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:mosaic:solved') }}</p>
          <p>{{ $t('puzzle:mosaic:solved_board') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/mosaic.page4.png" alt="Mosaic solved" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:mosaic:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:mosaic:control_mark_black')"></li>
        <li v-html="$t('puzzle:mosaic:control_mark_white')"></li>
        <li>{{ $t('puzzle:mosaic:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

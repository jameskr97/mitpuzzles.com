<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <p>{{ $t('puzzle:lightup:intro') }}</p>
          <p v-html="$t('puzzle:lightup:goal')"></p>
          <p>{{ $t('puzzle:lightup:board_example') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/lightup.page1.png" alt="Light Up board example" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:lightup:rule_illuminate')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/lightup.page2.png" alt="Light Up illumination" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:lightup:rule_numbered_cells')"></p>
          <p>{{ $t('puzzle:lightup:rule_numbered_cells_detail') }}</p>
          <p>{{ $t('puzzle:lightup:example_numbered') }}</p>
        </template>
        <template #board>
          <img src="/assets/instructions/lightup.page3.png" alt="Light Up numbered cells" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage>
        <template #instruction>
          <p v-html="$t('puzzle:lightup:rule_no_touch')"></p>
          <div v-html="$t('puzzle:lightup:example_invalid')"></div>
        </template>
        <template #board>
          <img src="/assets/instructions/lightup.page4.png" alt="Light Up invalid example" />
        </template>
      </InstructionPage>
    </template>

    <template #page5>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:lightup:solved')"></div>
          <div>{{ $t('puzzle:lightup:solved_board') }}</div>
        </template>
        <template #board>
          <img src="/assets/instructions/lightup.page5.png" alt="Light Up solved" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>{{ $t('puzzle:lightup:control_cycle') }}</div>
      <ul class="list-decimal ml-8">
        <li v-html="$t('puzzle:lightup:control_place_bulb')"></li>
        <li v-html="$t('puzzle:lightup:control_mark_cross')"></li>
        <li>{{ $t('puzzle:lightup:control_clear') }}</li>
      </ul>
    </template>
  </InstructionSlider>
</template>

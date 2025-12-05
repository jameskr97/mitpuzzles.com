<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
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
          <img src="/assets/instructions/aquarium.page1.png" alt="Aquarium board example" />
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
            <img src="/assets/instructions/aquarium.page2left.png" alt="Incorrect water placement" />
            <div class="text-red-500">Incorrect Placement</div>
          </div>
          <div class="flex flex-col gap-2 text-center">
            <img src="/assets/instructions/aquarium.page2right.png" alt="Correct water placement" />
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
          <img src="/assets/instructions/aquarium.page3.png" alt="Independent aquariums example" />
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
            <img src="/assets/instructions/aquarium.page4left.png" alt="Hint example left" />
          </div>
          <div class="flex flex-col gap-2 text-center">
            <img src="/assets/instructions/aquarium.page4right.png" alt="Hint example right" />
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
          <img src="/assets/instructions/aquarium.page5.png" alt="Solved aquarium" />
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

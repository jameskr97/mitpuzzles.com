<script setup lang="ts">
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <div>WIP Instructions</div>
        </template>
        <template #board>
          WIP
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <div>WIP</div>
    </template>
  </InstructionSlider>
</template>

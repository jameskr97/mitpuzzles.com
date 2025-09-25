<script setup lang="ts">
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { ACTIVE_GAMES } from "@/constants.ts";

const route = useRoute();
const layout = useGameLayout();
const game_type = route.meta.game_type as string;
const game_type_capitalized = computed(() => game_type.charAt(0).toUpperCase() + game_type.slice(1));
const game_entry = ACTIVE_GAMES[game_type];

const currentStep = ref(0);
defineProps({
  num_pages: { type: Number, required: false, default: 1 },
});
</script>

<template>
  <Dialog v-model:open="layout.instructions_visible.value">
    <DialogTrigger as-child>
      <slot name="trigger"></slot>
    </DialogTrigger>
    <DialogContent>
      <DialogHeader>
        <DialogTitle class="text-2xl">{{ game_type_capitalized }} instructions</DialogTitle>
      </DialogHeader>
      <component :is="game_entry.instructions" />
    </DialogContent>
  </Dialog>
</template>

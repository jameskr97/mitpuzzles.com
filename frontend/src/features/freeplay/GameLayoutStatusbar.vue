<script setup lang="ts">
/**
 * GameLayoutStatusbar - Status bar for freeplay games
 *
 * Shows tutorial toggle, current variant, and solved status.
 * Works with the GameController interface.
 */
import { computed } from "vue";
import type { GameController } from "@/core/games/types/game-controller";
import { Label } from "@/core/components/ui/label";
import { Badge } from "@/core/components/ui/badge";
import Container from "@/core/components/ui/Container.vue";
import { Switch } from "@/core/components/ui/switch";
import { getPuzzleDisplayName } from "@/utils";

const props = withDefaults(
  defineProps<{
    controller: GameController;
    show_tutorial?: boolean;
  }>(),
  {
    show_tutorial: false,
  },
);
const is_daily = props.controller.puzzle_type === "daily";

// Tutorial mode toggle handler
function toggle_tutorial_mode() {
  props.controller.ui.value.tutorial_mode = !props.controller.ui.value.tutorial_mode;
}

// Current variant display
const variant_display = computed(() => getPuzzleDisplayName(props.controller.current_variant.value));
</script>

<template>
  <Container class="w-full md:max-w-prose mx-auto h-12">
    <div class="m-0 p-0 grid grid-cols-3 text-xl">
      <!-- Tutorial Mode Toggle -->
      <div v-show="!is_daily" class="flex items-center gap-2">
        <Switch
          :model-value="controller.ui.value.tutorial_mode"
          @update:model-value="toggle_tutorial_mode"
          id="tutorial-toggle"
        />
        <Label for="tutorial-toggle" class="cursor-pointer font-normal">
          {{ $t("freeplay:settings.tutorial_mode") }}
        </Label>
      </div>

      <!-- Current Variant -->
      <span class="col-start-2 text-center items-center">
        {{ variant_display }}
      </span>

      <!-- solved status badge -->
      <Badge
        v-if="controller.ui.value.show_solved_state"
        :variant="controller.state.value.solved ? 'blue' : 'destructive'"
        class="justify-self-end text-nowrap text-base"
      >
        <span v-if="controller.state.value.solved">
          {{ $t("freeplay:status.solved") }}
        </span>
        <span v-else>
          {{ $t("freeplay:status.not_solved") }}
        </span>
      </Badge>
    </div>
  </Container>
</template>

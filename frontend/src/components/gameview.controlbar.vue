<script setup lang="ts">
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
import { onMounted, onUnmounted } from "vue";
import { getGameScale } from "@/store/scale.ts";
import GameviewControlBarTimer from "@/components/gameview.controlbar.timer.vue";

const layout = useGameLayout();
const puzzle = await useCurrentPuzzle();
const { scale } = getGameScale();
////////////////////////////////////////////////////////////////////////
//// puzzle difficulty dropdown
function getDisplayName(parts?: string[]): string {
  if (!parts) return "undefined";
  if (parts.length < 2) return parts[0];
  const name = parts
    .slice(1)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
  return `${parts[0]} ${name}`;
}

function onDifficultySelect(diff: string[]) {
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  puzzle.selected_variant.value = diff;
  puzzle.request_new_puzzle();
}

////////////////////////////////////////////////////////////////////////
//// puzzle timer view
onMounted(() => puzzle.timer.start());
onUnmounted(() => puzzle.timer.stop());
</script>

<template>
  <div class="flex flex-col">
    <div class="flex flex-col items-center w-full md:w-4/5 2xl:w-2/4 mx-auto justify-around gap-2 px-2">
      <div class="flex flex-row w-full">
        <v-icon
          name="hi-information-circle"
          :scale="1.5"
          class="mr-2 cursor-pointer"
          @click="layout.toggle_instructions()"
        />
        <div class="tooltip tooltip-bottom w-full" data-tip="Resize Game Board">
          <input v-model="scale" type="range" min="0" max="100" class="range w-full user-select-none" />
        </div>
        <div class="divider divider-horizontal mx-2"></div>
        <GameviewControlBarTimer />
      </div>

      <!-- Buttons -->
      <div class="grid grid-cols-2 lg:grid-cols-4 w-full gap-1">
        <div class="dropdown dropdown-center">
          <button ref="difficulty-dropdown" tabindex="0" role="button" class="btn btn-secondary w-full">
            Difficulty
            <v-icon name="md-arrowdropdown" />
          </button>
          <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-1 w-full mt-2 p-2 shadow-sm">
            <li v-if="puzzle.available_variants.value.length === 0">
              <a disabled>No variants available</a>
            </li>
            <li
              v-for="variant in puzzle.available_variants.value"
              :key="variant[0] + '.' + variant[1]"
              @click="onDifficultySelect(variant)"
            >
              <a>{{ getDisplayName(variant) }}</a>
            </li>
          </ul>
        </div>
        <button class="btn btn-info" @click="puzzle.request_new_puzzle">New Puzzle</button>
        <button
          class="btn btn-error"
          :disabled="puzzle.is_solved.value == true"
          @click="puzzle.session.cmd_puzzle_reset"
        >
          Clear
        </button>
        <button
          class="btn btn-success"
          :disabled="puzzle.is_solved.value == true"
          @click="puzzle.session.cmd_puzzle_submit"
        >
          Submit
        </button>
      </div>

      <!-- Game variant display -->
      <div class="m-0 p-0">{{ getDisplayName(puzzle.selected_variant.value) }}</div>
    </div>
  </div>
</template>

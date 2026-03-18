<script setup lang="ts">
/**
 * GameLayoutControlbar - Control bar for freeplay games
 *
 * Works with the GameController interface.
 */
import { computed, onMounted, onUnmounted } from "vue";
import type { GameController } from "@/core/games/types/game-controller";
import Container from "@/core/components/ui/Container.vue";
import { Slider } from "@/core/components/ui/slider";
import { Button } from "@/core/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/core/components/ui/dropdown-menu";
import { getPuzzleDisplayName } from "@/utils";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore";

const is_dev = import.meta.env.DEV;

const props = defineProps<{
  controller: GameController;
}>();

const puzzle_type = props.controller.puzzle_type;
const scale_store = usePuzzleScaleStore();
const metadata_store = usePuzzleMetadataStore();
const progress_store = usePuzzleProgressStore();
const history_store = usePuzzleHistoryStore();

// Scale slider
const current_scale = computed({
  get: () => [scale_store.getScale(puzzle_type)],
  set: (value: number[]) => scale_store.setScale(puzzle_type, value[0]),
});

// Timer display (uses dynamic progress key from controller)
const formatted_time = computed(() => props.controller.formatted_time.value);

// Difficulty selection
async function on_difficulty_select(variant: string[]) {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
  metadata_store.set_selected_variant(puzzle_type, variant);
  await props.controller.request_new_puzzle();
}

// Keyboard shortcuts for zoom
onMounted(() => {
  function handle_keydown(e: KeyboardEvent) {
    if (e.key === "+" || e.key === "=" || e.key === "-") {
      const increment = e.key === "+" || e.key === "=" ? 5 : -5;
      e.preventDefault();
      const new_scale = Math.max(0, Math.min(100, current_scale.value[0] + increment));
      scale_store.setScale(puzzle_type, new_scale);
    }
  }

  window.addEventListener("keydown", handle_keydown);
  onUnmounted(() => window.removeEventListener("keydown", handle_keydown));
});

// Download payload (dev mode only)
function download_payload() {
  const payload = history_store.get_upload_payload(puzzle_type, "freeplay");
  if (!payload) {
    console.warn("No payload to download");
    return;
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${puzzle_type}-${payload.puzzle_id}-payload.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
</script>

<template>
  <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
    <div class="flex flex-col">
      <!-- Zoom + Timer row for DESKTOP -->
      <div class="flex-row w-full items-center hidden md:flex">
        <v-icon name="co-magnifying-glass" :scale="1.5" />
        <Slider :min="0" :max="100" :step="1" class="mx-2" v-model="current_scale" />
        <span class="font-mono text-lg text-right">{{ formatted_time }}</span>
      </div>

      <!-- Zoom + Timer row for MOBILE -->
      <div class="flex flex-row w-full items-center md:hidden">
        <span class="font-mono text-lg text-center w-full">{{ formatted_time }}</span>
      </div>

      <!-- Buttons row -->
      <div class="grid grid-cols-2 lg:grid-cols-4 w-full gap-1 mt-2">
        <!-- Difficulty dropdown -->
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button class="w-full" variant="outline">
              <span>{{ $t("freeplay:control.difficulty") }}</span>
              <v-icon name="md-arrowdropdown" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent class="w-full">
            <DropdownMenuItem
              v-for="variant in metadata_store.getVariants(puzzle_type)"
              :key="variant[0] + '.' + variant[1]"
              @click="on_difficulty_select(variant)"
            >
              <span>{{ getPuzzleDisplayName(variant) }}</span>
              <v-icon
                name="bi-check"
                v-if="metadata_store.doesMatchCurrentVariant(puzzle_type, variant)"
              />
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <!-- New Puzzle button (hidden in daily mode) -->
        <Button v-if="!controller.is_daily.value" @click="controller.request_new_puzzle">
          {{ $t("freeplay:control.new_puzzle") }}
        </Button>

        <!-- Clear button -->
        <Button
          variant="destructive"
          :disabled="controller.state.value.solved === true"
          @click="controller.clear_puzzle"
        >
          {{ $t("ui:action.clear") }}
        </Button>

        <!-- Submit button (becomes Download in dev mode when solved) -->
        <Button
          v-if="is_dev && controller.state.value.solved === true"
          variant="outline"
          @click="download_payload"
        >
          Download Payload
        </Button>
        <Button
          v-else
          variant="success"
          :disabled="controller.state.value.solved === true"
          @click="controller.check_solution"
        >
          {{ $t("ui:action.submit") }}
        </Button>
      </div>
    </div>
  </Container>
</template>

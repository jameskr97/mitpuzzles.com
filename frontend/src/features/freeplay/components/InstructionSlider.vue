<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, useSlots } from "vue";
import { useGameLayout } from "@/core/composables/useGameLayout.ts";
import { Button } from "@/core/components/ui/button";
import ProgressBar from "@/core/components/ProgressBar.vue";
import InstructionPage from "./InstructionPage.vue";

const layout = useGameLayout();
const slots = useSlots();
const current_step = ref(0);

// Auto-detect number of pages from slots (page1, page2, etc.)
const num_pages = computed(() => {
  let count = 0;
  while (slots[`page${count + 1}`]) {
    count++;
  }
  return count;
});

const go_previous = () => {
  if (current_step.value > 0) {
    current_step.value--;
  }
};

const go_next = () => {
  if (current_step.value < num_pages.value) {
    current_step.value++;
  } else if (current_step.value === num_pages.value) {
    done();
  }
};

const done = () => {
  layout.instructions_visible.value = false;
  setTimeout(() => {
    current_step.value = 0;
  }, 300);
};

const handle_keydown = (event: KeyboardEvent) => {
  if (!layout.instructions_visible.value) return;
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    go_previous();
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    go_next();
  }
};

onMounted(() => {
  window.addEventListener("keydown", handle_keydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handle_keydown);
});
</script>

<template>
  <div class="flex flex-col h-[60vh] max-h-[500px] touch-manipulation">
    <!-- Content area - fills available space, scrolls if needed -->
    <div class="flex-1 overflow-y-auto px-1 min-h-0">
      <slot
        v-if="current_step < num_pages"
        :name="`page${current_step + 1}`"
      ></slot>

      <!-- Final page: controls - fills the whole modal -->
      <div v-else class="text-lg flex flex-col gap-4 h-full">
        <div>
          <div class="font-bold">
            {{ $t("freeplay:instructions.game_controls") }}
          </div>
          <slot name="controls"></slot>
          <div v-html="$t('freeplay:instructions.submit_hint')"></div>
        </div>
        <div>
          <div class="font-bold">
            {{ $t("freeplay:instructions.misc_info") }}
          </div>
          <ul class="list-none">
            <li class="flex items-center gap-2">
              <v-icon name="hi-information-circle" :scale="1.2" />
              {{ $t("freeplay:instructions.info_circle_hint") }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Navigation footer -->
    <div
      class="flex-shrink-0 grid grid-cols-[auto_1fr_auto] items-center gap-4 pt-4"
    >
      <Button variant="outline" :disabled="current_step === 0" @click="go_previous">
        <kbd class="kbd kbd-sm">←</kbd>
      </Button>

      <ProgressBar
        :current_step="current_step + 1"
        :segments="num_pages + 1"
        container_class="mx-2"
      />

      <Button variant="outline" @click="go_next">
        <kbd class="kbd kbd-sm">→</kbd>
      </Button>
    </div>
  </div>
</template>

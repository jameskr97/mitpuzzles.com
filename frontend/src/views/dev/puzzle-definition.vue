<script setup lang="ts">
import Container from "@/components/ui/Container.vue";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { usePuzzleDefinitionStore } from "@/store/puzzle/usePuzzleDefinitionStore.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import PuzzleRenderer from "@/components/PuzzleRenderer.vue";
import { PuzzleConverter } from "@/services/game/engines/translator.ts";

const route = useRoute();
const enteredID = ref<number>();
const currentPuzzle = ref<PuzzleDefinition | null>(null);
const puzzle = usePuzzleDefinitionStore();

const state_initial = computed(() => ({
  definition: currentPuzzle.value!,
  board: PuzzleConverter.fromResearch(currentPuzzle.value!.initial_state!, currentPuzzle.value!.puzzle_type!) || null,
}));

const state_solved = computed(() => ({
  definition: currentPuzzle.value!,
  board: PuzzleConverter.fromResearch(currentPuzzle.value!.solution!, currentPuzzle.value!.puzzle_type!) || null,
}));

if (route.query.id) {
  enteredID.value = parseInt(route.query.id as string);
  getPuzzle();
}

async function getPuzzle() {
  if (!enteredID.value) return;
  try {
    const response = await fetch(`/api/puzzle/definition/${enteredID.value}?include_solution=true`);
    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();
    currentPuzzle.value = data as PuzzleDefinition;
  } catch {
    console.log("Failed to fetch puzzle definition. Please check the ID and try again.");
    return;
  }
}
function formatJSON(obj: any): string {
  const jsonString = JSON.stringify(
    obj,
    (key, value) => {
      if (Array.isArray(value) && value.length > 0 && !Array.isArray(value[0])) {
        return `[${value.join(", ")}]`;
      }
      return value;
    },
    2,
  ).replace(/"\[([^\]]+)\]"/g, "[$1]");

  return jsonString
    .replace(/"([\w_]+)":/g, '<span class="json-key">"$1"</span>:')
    .replace(/:\s*(".*?")/g, ': <span class="json-string">$1</span>')
    .replace(/:\s*(-?\d+(?:\.\d+)?)/g, ': <span class="json-number">$1</span>')
    .replace(/:\s*(true|false)/g, ': <span class="json-boolean">$1</span>')
    .replace(/(\[|\]|\{|\})/g, '<span class="json-bracket">$1</span>');
}
</script>

<template>
  <Container class="p-2 m-2">
    <div class="flex flex-col">
      <h1 class="text-3xl font-bold mb-4">Puzzle Definition</h1>
      <div class="flex flex-row">
        <Input v-model="enteredID" type="number" placeholder="1234" class="w-50" required @keyup.enter="getPuzzle" />
        <Button variant="outline" class="ml-2" @click="getPuzzle"> Get Puzzle Definition </Button>
      </div>
    </div>
  </Container>
  <div class="grid grid-cols-2 gap-2 m-2">

    <!-- Rendered Puzzle Definition -->
    <Container>
      <div class="flex flex-col">
        <div class="text-2xl font-bold underline text-center">Rendered Puzzle Definition</div>
        <div>
          <PuzzleRenderer
            v-if="currentPuzzle"
            :definition="currentPuzzle"
            :state="state_initial"
            :scale="0.8"
            class="mx-auto"
          />
          <p v-else class="text-center">Enter an ID to view a puzzle</p>
        </div>
      </div>
    </Container>

    <!-- Rendered Puzzle Solution -->
    <Container>
      <div class="flex flex-col">
        <div class="text-2xl font-bold underline text-center">Rendered Puzzle Solution</div>
        <div>
          <PuzzleRenderer
            v-if="currentPuzzle"
            :definition="currentPuzzle"
            :state="state_solved"
            :scale="0.8"
            class="mx-auto"
          />
          <p v-else class="text-center">Enter an ID to view a puzzle</p>
        </div>
      </div>
    </Container>

    <!-- Puzzle Definition Viewer -->
    <Container class="col-span-2">
      <div class="flex flex-col">
        <div class="text-2xl font-bold underline text-center">PuzzleDefinition Source</div>
        <div>
          <div v-if="currentPuzzle" class="json-viewer rounded p-2">
            <pre v-html="formatJSON(currentPuzzle)"></pre>
          </div>
          <p v-else class="text-center">Enter an ID to view a puzzle</p>
        </div>
      </div>
    </Container>
  </div>
</template>

<style scoped>
.json-viewer,
.json-viewer * {
  font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace !important;
  font-size: 12px;
  background: #1f1f28; /* sumiInk3 */
  color: #dcd7ba; /* fujiWhite */
}

/* Syntax Highlighting Colors */
.json-viewer :deep(.json-key) {
  color: #7e9cd8;
} /* crystalBlue */
.json-viewer :deep(.json-string) {
  color: #98bb6c;
} /* springGreen */
.json-viewer :deep(.json-number) {
  color: #d27e99;
} /* sakuraPink */
.json-viewer :deep(.json-boolean) {
  color: #e46876;
} /* waveRed */
.json-viewer :deep(.json-bracket) {
  color: #e6c384;
} /* carpYellow */
</style>

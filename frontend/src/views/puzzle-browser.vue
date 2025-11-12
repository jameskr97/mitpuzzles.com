<script setup lang="ts">
import { computed, onMounted, ref, watch, shallowRef } from "vue";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore";
import Container from "@/components/ui/Container.vue";
import { api } from "@/services/axios";
import PuzzleRenderer from "@/components/PuzzleRenderer.vue";
import PuzzleBrowserItem from "@/features/analysis/components/PuzzleBrowserItem.vue";
import { PuzzleConverter } from "@/services/game/engines/translator.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";

// Store for puzzle metadata
const puzzleMetadataStore = usePuzzleMetadataStore();

// state
const loading_filters = ref(true);
const loading_puzzles = ref(false);
const selected_puzzle_types = ref<Set<string>>(new Set());
const selected_puzzle_sizes = ref<Set<string>>(new Set());
const selected_difficulties = ref<Set<string>>(new Set());
const has_attempts_filter = ref<"all" | "with_attempts" | "without_attempts">("all");
const grid_size = ref<"small" | "medium" | "large">("medium");
const all_puzzles = ref<any[]>([]);
const total_count = ref(0);
const current_offset = ref(0);
const has_more = ref(true);
const dynamic_filter_options = ref<any>(null);

// modal state for puzzle definition viewer
const show_definition_modal = ref(false);
const selected_puzzle_definition = ref<PuzzleDefinition | null>(null);
const loading_definition = ref(false);

// computed states for puzzle rendering
const state_initial = computed(() => {
  if (!selected_puzzle_definition.value) return null;
  return {
    definition: selected_puzzle_definition.value,
    board:
      PuzzleConverter.fromResearch(
        selected_puzzle_definition.value.initial_state!,
        selected_puzzle_definition.value.puzzle_type!,
      ) || null,
  };
});

const state_solved = computed(() => {
  if (!selected_puzzle_definition.value) return null;
  return {
    definition: selected_puzzle_definition.value,
    board:
      PuzzleConverter.fromResearch(
        selected_puzzle_definition.value.solution!,
        selected_puzzle_definition.value.puzzle_type!,
      ) || null,
  };
});

// grid configuration based on size
const gridConfig = computed(() => {
  switch (grid_size.value) {
    case "small":
      return { cols: "grid-cols-8", puzzlesPerPage: 64 };
    case "medium":
      return { cols: "grid-cols-6", puzzlesPerPage: 36 };
    case "large":
      return { cols: "grid-cols-4", puzzlesPerPage: 16 };
    default:
      return { cols: "grid-cols-6", puzzlesPerPage: 36 };
  }
});

// Color mapping for puzzle types
const puzzle_colors: Record<string, string> = {
  minesweeper: "bg-gray-500",
  sudoku: "bg-blue-500",
  tents: "bg-green-500",
  kakurasu: "bg-purple-500",
  lightup: "bg-yellow-400",
  nonograms: "bg-red-500",
  battleships: "bg-slate-700",
};

// Get available puzzle types
const available_puzzle_types = computed(() => {
  return Object.keys(puzzleMetadataStore.variants);
});

// Get selected counts for display
const selected_types_count = computed(() => selected_puzzle_types.value.size);
const selected_sizes_count = computed(() => selected_puzzle_sizes.value.size);
const selected_difficulties_count = computed(() => selected_difficulties.value.size);

// API function to fetch puzzles
const fetch_puzzles = async (append: boolean = false) => {
  loading_puzzles.value = true;

  try {
    const params: Record<string, string | string[]> = {
      limit: gridConfig.value.puzzlesPerPage.toString(),
      offset: current_offset.value.toString(),
    };

    // add all selected filters
    if (selected_puzzle_types.value.size > 0) params.puzzle_type = Array.from(selected_puzzle_types.value);
    if (selected_puzzle_sizes.value.size > 0) params.puzzle_size = Array.from(selected_puzzle_sizes.value);
    if (selected_difficulties.value.size > 0) params.puzzle_difficulty = Array.from(selected_difficulties.value);
    if (has_attempts_filter.value !== "all") params.has_attempts = has_attempts_filter.value;

    const response = await api.get("/api/puzzle/browse", {
      params,
      paramsSerializer: {
        indexes: null, // This removes the [] brackets from array parameters
      },
    });
    const data = response.data;

    if (append) {
      all_puzzles.value = [...all_puzzles.value, ...data.puzzles];
    } else {
      all_puzzles.value = data.puzzles;
    }

    total_count.value = data.total_count;
    has_more.value = data.has_more;
    current_offset.value = data.offset + data.limit;
  } catch (error) {
    console.error("Failed to fetch puzzles:", error);
  } finally {
    loading_puzzles.value = false;
  }
};

// Fetch dynamic filter options
const fetch_filter_options = async () => {
  try {
    const params: Record<string, string | string[]> = {};

    // add current filter selections
    if (selected_puzzle_types.value.size > 0) params.puzzle_type = Array.from(selected_puzzle_types.value);
    if (selected_puzzle_sizes.value.size > 0) params.puzzle_size = Array.from(selected_puzzle_sizes.value);
    if (selected_difficulties.value.size > 0) params.puzzle_difficulty = Array.from(selected_difficulties.value);
    if (has_attempts_filter.value !== "all") params.has_attempts = has_attempts_filter.value;

    const response = await api.get("/api/puzzle/filter-options", {
      params,
      paramsSerializer: { indexes: null },
    });

    dynamic_filter_options.value = response.data;
  } catch (error) {
    console.error("Failed to fetch filter options:", error);
  }
};

// Since filtering is now done server-side, we just display all fetched puzzles
const displayed_puzzles = computed(() => all_puzzles.value);
// Show loading indicator when fetching more puzzles
const show_load_more = computed(() => has_more.value && !loading_puzzles.value);

// Toggle filter selections
const toggle_puzzle_type = (type: string) => {
  if (selected_puzzle_types.value.has(type)) {
    selected_puzzle_types.value.delete(type);
  } else {
    selected_puzzle_types.value.add(type);
  }
};

const toggle_puzzle_size = (size: string) => {
  if (selected_puzzle_sizes.value.has(size)) {
    selected_puzzle_sizes.value.delete(size);
  } else {
    selected_puzzle_sizes.value.add(size);
  }
};

const toggle_difficulty = (difficulty: string) => {
  if (selected_difficulties.value.has(difficulty)) {
    selected_difficulties.value.delete(difficulty);
  } else {
    selected_difficulties.value.add(difficulty);
  }
};

const clear_all_filters = () => {
  selected_puzzle_types.value.clear();
  selected_puzzle_sizes.value.clear();
  selected_difficulties.value.clear();
  has_attempts_filter.value = "all";
  grid_size.value = "medium";
};

// Load more puzzles
const load_more = async () => {
  await fetch_puzzles(true);
};

// Handle puzzle click to show definition
const show_puzzle_definition = async (puzzle: any) => {
  loading_definition.value = true;
  show_definition_modal.value = true;

  try {
    // Fetch the full puzzle definition with solution
    const response = await api.get(`/api/puzzle/definition/${puzzle.id}?include_solution=true`);
    selected_puzzle_definition.value = response.data as PuzzleDefinition;
  } catch (error) {
    console.error("Failed to fetch puzzle definition:", error);
    // Fall back to showing the puzzle without solution
    selected_puzzle_definition.value = puzzle as PuzzleDefinition;
  } finally {
    loading_definition.value = false;
  }
};

// Close modal
const close_definition_modal = () => {
  show_definition_modal.value = false;
  selected_puzzle_definition.value = null;
};

// JSON formatting function (from puzzle-definition.vue)
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

// Watch for filter changes and refetch both puzzles and filter options
watch(
  [selected_puzzle_types, selected_puzzle_sizes, selected_difficulties],
  async () => {
    current_offset.value = 0;
    await fetch_puzzles(false); // append=false, replace current puzzles
    await fetch_filter_options(); // update available filter options
  },
  { deep: true },
);

// Watch attempts filter separately (only affects puzzle fetching, not filter options)
watch(has_attempts_filter, async () => {
  current_offset.value = 0;
  await fetch_puzzles(false); // append=false, replace current puzzles
  // Don't update filter options for attempts changes to avoid recursive updates
});

// Watch grid size separately (only affects puzzle fetching, not filter options)
watch(grid_size, async () => {
  current_offset.value = 0;
  await fetch_puzzles(false);
});

// Initialize
onMounted(async () => {
  await puzzleMetadataStore.initializeStore();

  // fetch initial dynamic filter options
  await fetch_filter_options();
  loading_filters.value = false;

  // Then load puzzles (this can take longer)
  loading_puzzles.value = true;
  await fetch_puzzles(); // Load initial puzzles
});
</script>

<template>
  <div class="flex h-screen">
    <!-- Left Sidebar -->
    <Container class="w-1/5 min-w-[200px] my-2 p-2 overflow-y-auto">
      <h2 class="text-lg font-semibold text-center">Filters</h2>
      <!-- Puzzle Type Filters -->
      <div class="space-y-1">
        <!-- Listbox Header -->
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-medium text-gray-700">Puzzle Types</h3>
          <span v-if="selected_types_count > 0" class="text-xs text-blue-600 font-medium">
            {{ selected_types_count }} selected
          </span>
        </div>

        <div v-if="loading_filters" class="text-gray-500 text-sm">Loading puzzle types...</div>

        <!-- Listbox Container -->
        <div v-else-if="dynamic_filter_options" class="border border-gray-200 rounded-lg overflow-hidden">
          <div
            v-for="typeOption in dynamic_filter_options.puzzle_types"
            :key="typeOption.value"
            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
            :class="{
              'bg-blue-50 border-blue-200': selected_puzzle_types.has(typeOption.value),
              'opacity-50 cursor-not-allowed': typeOption.count === 0,
            }"
            :data-state="selected_puzzle_types.has(typeOption.value) ? 'checked' : 'unchecked'"
            @click="typeOption.count > 0 && toggle_puzzle_type(typeOption.value)"
            role="option"
            :aria-selected="selected_puzzle_types.has(typeOption.value)"
          >
            <!-- Selection Indicator -->
            <div class="flex items-center justify-center w-3 h-3 mr-2">
              <svg
                v-if="selected_puzzle_types.has(typeOption.value)"
                class="w-2.5 h-2.5 text-blue-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>

            <!-- Label -->
            <span class="flex-1 text-xs font-medium text-gray-900 capitalize">
              {{ typeOption.value }}
            </span>

            <!-- Count -->
            <span class="text-xs text-gray-500 mr-2">{{ typeOption.count }}</span>

            <!-- Color Badge -->
            <div :class="puzzle_colors[typeOption.value] || 'bg-gray-400'" class="w-2.5 h-2.5 rounded-full"></div>
          </div>
        </div>
      </div>

      <!-- Puzzle Size Filters -->
      <div class="space-y-1 mt-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-medium text-gray-700">Puzzle Sizes</h3>
          <span v-if="selected_sizes_count > 0" class="text-xs text-blue-600 font-medium">
            {{ selected_sizes_count }} selected
          </span>
        </div>

        <div v-if="loading_filters" class="text-gray-500 text-sm">Loading sizes...</div>

        <div v-else-if="dynamic_filter_options" class="border border-gray-200 rounded-lg overflow-hidden">
          <div
            v-for="sizeOption in dynamic_filter_options.puzzle_sizes"
            :key="sizeOption.value"
            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
            :class="{
              'bg-blue-50 border-blue-200': selected_puzzle_sizes.has(sizeOption.value),
              'opacity-50 cursor-not-allowed': sizeOption.count === 0,
            }"
            :data-state="selected_puzzle_sizes.has(sizeOption.value) ? 'checked' : 'unchecked'"
            @click="sizeOption.count > 0 && toggle_puzzle_size(sizeOption.value)"
            role="option"
            :aria-selected="selected_puzzle_sizes.has(sizeOption.value)"
          >
            <div class="flex items-center justify-center w-3 h-3 mr-2">
              <svg
                v-if="selected_puzzle_sizes.has(sizeOption.value)"
                class="w-2.5 h-2.5 text-blue-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <span class="flex-1 text-xs font-medium text-gray-900">
              {{ sizeOption.value }}
            </span>
            <span class="text-xs text-gray-500">{{ sizeOption.count }}</span>
          </div>
        </div>
      </div>

      <!-- Difficulty Filters -->
      <div class="space-y-1 mt-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-medium text-gray-700">Difficulty</h3>
          <span v-if="selected_difficulties_count > 0" class="text-xs text-blue-600 font-medium">
            {{ selected_difficulties_count }} selected
          </span>
        </div>

        <div v-if="loading_filters" class="text-gray-500 text-sm">Loading difficulties...</div>

        <div v-else-if="dynamic_filter_options" class="border border-gray-200 rounded-lg overflow-hidden">
          <div
            v-for="difficultyOption in dynamic_filter_options.puzzle_difficulties"
            :key="difficultyOption.value"
            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
            :class="{
              'bg-blue-50 border-blue-200': selected_difficulties.has(difficultyOption.value),
              'opacity-50 cursor-not-allowed': difficultyOption.count === 0,
            }"
            :data-state="selected_difficulties.has(difficultyOption.value) ? 'checked' : 'unchecked'"
            @click="difficultyOption.count > 0 && toggle_difficulty(difficultyOption.value)"
            role="option"
            :aria-selected="selected_difficulties.has(difficultyOption.value)"
          >
            <div class="flex items-center justify-center w-3 h-3 mr-2">
              <svg
                v-if="selected_difficulties.has(difficultyOption.value)"
                class="w-2.5 h-2.5 text-blue-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <span class="flex-1 text-xs font-medium text-gray-900 capitalize">
              {{ difficultyOption.value }}
            </span>
            <span class="text-xs text-gray-500">{{ difficultyOption.count }}</span>
          </div>
        </div>
      </div>

      <!-- Has Attempts Filter -->
      <div class="space-y-1 mt-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-medium text-gray-700">Attempts</h3>
        </div>

        <div v-if="dynamic_filter_options" class="border border-gray-200 rounded-lg overflow-hidden">
          <div
            v-for="attemptOption in dynamic_filter_options.attempts_options"
            :key="attemptOption.value"
            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
            :class="{
              'bg-blue-50 border-blue-200': has_attempts_filter === attemptOption.value,
            }"
            @click="has_attempts_filter = attemptOption.value"
            role="option"
            :aria-selected="has_attempts_filter === attemptOption.value"
          >
            <div class="flex items-center justify-center w-3 h-3 mr-2">
              <svg
                v-if="has_attempts_filter === attemptOption.value"
                class="w-2.5 h-2.5 text-blue-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <span class="flex-1 text-xs font-medium text-gray-900">
              {{
                attemptOption.value === "all"
                  ? "All Puzzles"
                  : attemptOption.value === "with_attempts"
                    ? "Has Attempts"
                    : "No Attempts"
              }}
            </span>
            <span class="text-xs text-gray-500">{{ attemptOption.count }}</span>
          </div>
        </div>
      </div>

      <!-- Clear Filters -->
      <button
        @click="clear_all_filters"
        class="mt-4 w-full px-3 py-2 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors font-medium"
      >
        Clear All Filters
      </button>
    </Container>

    <!-- Main Content Area -->
    <div class="flex flex-col gap-2 m-2 w-full">
      <Container>
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold">Puzzle Browser</h1>

          <!-- Puzzle Count -->
          <div class="text-sm text-gray-600">
            Showing {{ displayed_puzzles.length }} of {{ total_count }} puzzles
          </div>

          <!-- Grid Size Control -->
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600">Grid size:</span>
            <select
              v-model="grid_size"
              class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="small">Small (8 across)</option>
              <option value="medium">Medium (6 across)</option>
              <option value="large">Large (4 across)</option>
            </select>
          </div>
        </div>
      </Container>

      <Container class="flex-1 p-6 overflow-y-auto">
        <!-- Loading State -->
        <div v-if="loading_puzzles && all_puzzles.length === 0" class="flex items-center justify-center h-64">
          <div class="text-xl text-gray-500">Loading puzzles...</div>
        </div>

        <!-- Puzzle Grid -->
        <div v-else>
          <!-- Grid -->
          <div class="grid gap-2 mb-8" :class="gridConfig.cols">
            <PuzzleBrowserItem
              v-for="puzzle in displayed_puzzles"
              :key="puzzle.id"
              :puzzle="puzzle"
              @click="show_puzzle_definition"
            />
          </div>

          <!-- Load More Button -->
          <div v-if="show_load_more" class="flex justify-center">
            <button
              @click="load_more"
              class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Load More
            </button>
          </div>

          <!-- Loading More -->
          <div v-if="loading_puzzles" class="flex justify-center">
            <div class="px-6 py-3 text-gray-500">Loading more puzzles...</div>
          </div>

          <!-- No Results -->
          <div v-if="!loading_puzzles && displayed_puzzles.length === 0" class="text-center text-gray-500 mt-8">
            No puzzles found with the selected filters.
          </div>
        </div>
      </Container>
    </div>
  </div>

  <!-- Puzzle Definition Modal -->
  <div
    v-if="show_definition_modal"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
    @click="close_definition_modal"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[95vh] overflow-hidden" @click.stop>
      <!-- Modal Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          Puzzle Definition
          <span v-if="selected_puzzle_definition" class="text-sm font-normal text-gray-500 ml-2">
            {{ selected_puzzle_definition.puzzle_type }} -
            {{ selected_puzzle_definition.rows }}x{{selected_puzzle_definition.cols }}
          </span>
        </h3>
        <button @click="close_definition_modal" class="text-gray-400 hover:text-gray-600 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-auto max-h-[calc(95vh-120px)]">
        <div v-if="loading_definition" class="flex justify-center items-center h-64">
          <div class="text-gray-500">Loading puzzle definition...</div>
        </div>

        <div v-else-if="selected_puzzle_definition" class="grid grid-cols-2 gap-4">
          <!-- Rendered Puzzle Definition -->
          <Container>
            <div class="flex flex-col">
              <div class="text-xl font-bold underline text-center mb-4">Initial State</div>
              <div class="flex justify-center">
                <PuzzleRenderer
                  v-if="state_initial"
                  :definition="selected_puzzle_definition"
                  :state="state_initial"
                  :scale="0.6"
                  class="mx-auto"
                />
              </div>
            </div>
          </Container>

          <!-- Rendered Puzzle Solution -->
          <Container>
            <div class="flex flex-col">
              <div class="text-xl font-bold underline text-center mb-4">Solution State</div>
              <div class="flex justify-center">
                <PuzzleRenderer
                  v-if="state_solved"
                  :definition="selected_puzzle_definition"
                  :state="state_solved"
                  :scale="0.6"
                  class="mx-auto"
                />
                <div v-else class="text-center text-gray-500">Solution not available</div>
              </div>
            </div>
          </Container>

          <!-- Puzzle Definition JSON -->
          <Container class="col-span-2">
            <div class="flex flex-col">
              <div class="text-xl font-bold underline text-center mb-4">Puzzle Definition JSON</div>
              <div class="json-viewer rounded p-4 max-h-80 overflow-auto">
                <pre v-html="formatJSON(selected_puzzle_definition)"></pre>
              </div>
            </div>
          </Container>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="flex justify-end p-6 border-t border-gray-200">
        <button
          @click="close_definition_modal"
          class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
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
.json-viewer :deep(.json-key) { color: #7e9cd8; } /* crystalBlue */
.json-viewer :deep(.json-string) { color: #98bb6c; } /* springGreen */
.json-viewer :deep(.json-number) { color: #d27e99; } /* sakuraPink */
.json-viewer :deep(.json-boolean) { color: #e46876; } /* waveRed */
.json-viewer :deep(.json-bracket) { color: #e6c384; } /* carpYellow */
</style>

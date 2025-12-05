<script setup lang="ts">
import { Download, Plus, ChevronDown, ChevronRight } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";

import Container from "@/core/components/ui/Container.vue";
import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import { Input } from "@/core/components/ui/input";
import { ACTIVE_GAMES } from "@/constants";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/core/components/ui/dialog";
import PuzzleRenderer from "@/core/components/PuzzleRenderer.vue";
import {
  get_priority_puzzles_grouped,
  add_priority_puzzle,
  get_priority_group_export_url,
  type PriorityGroup,
} from "@/core/services/app";
import { api } from "@/core/services/axios";
import { download_blob } from "@/utils";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";

const groups = ref<PriorityGroup[]>([]);
const total_groups = ref(0);
const total_puzzles = ref(0);
const loading = ref(false);
const error = ref<string | null>(null);

// Track which groups are expanded
const expanded_groups = ref<Set<string>>(new Set());

// Cache for puzzle definitions (puzzle_id -> definition)
const puzzle_definitions = ref<Map<string, PuzzleDefinition>>(new Map());

// Track which groups are currently loading definitions
const loading_groups = ref<Set<string>>(new Set());

// Add puzzle dialog
const add_dialog_open = ref(false);
const new_puzzle_id = ref("");
const adding = ref(false);
const add_error = ref<string | null>(null);


const get_group_key = (group: PriorityGroup) => {
  return `${group.puzzle_type}-${group.puzzle_size}-${group.puzzle_difficulty || 'none'}`;
};

const format_group_title = (group: PriorityGroup) => {
  const parts = [
    group.puzzle_type.charAt(0).toUpperCase() + group.puzzle_type.slice(1),
    group.puzzle_size,
  ];
  if (group.puzzle_difficulty) {
    parts.push(group.puzzle_difficulty.charAt(0).toUpperCase() + group.puzzle_difficulty.slice(1));
  }
  return parts.join(" · ");
};

const is_known_puzzle_type = (puzzle_type: string) => {
  return puzzle_type in ACTIVE_GAMES;
};

// Sort groups: known types first, unknown types at bottom
const sorted_groups = computed(() => {
  return [...groups.value].sort((a, b) => {
    const a_known = is_known_puzzle_type(a.puzzle_type);
    const b_known = is_known_puzzle_type(b.puzzle_type);
    if (a_known && !b_known) return -1;
    if (!a_known && b_known) return 1;
    return 0;
  });
});

const is_group_expanded = (group: PriorityGroup) => {
  return expanded_groups.value.has(get_group_key(group));
};

const is_group_loading = (group: PriorityGroup) => {
  return loading_groups.value.has(get_group_key(group));
};

// Fetch a single puzzle definition (with solution for admin rendering)
const fetch_puzzle_definition = async (puzzle_id: string): Promise<PuzzleDefinition | null> => {
  // Check cache first
  if (puzzle_definitions.value.has(puzzle_id)) {
    return puzzle_definitions.value.get(puzzle_id)!;
  }

  try {
    const response = await api.get<PuzzleDefinition>(`/api/puzzle/definition/${puzzle_id}?include_solution=true`);
    puzzle_definitions.value.set(puzzle_id, response.data);
    return response.data;
  } catch (err) {
    console.warn(`Failed to fetch puzzle definition for ${puzzle_id}:`, err);
    return null;
  }
};

// Toggle group expansion and fetch definitions if needed
const toggle_group = async (group: PriorityGroup) => {
  const key = get_group_key(group);

  if (expanded_groups.value.has(key)) {
    expanded_groups.value.delete(key);
    // Force reactivity
    expanded_groups.value = new Set(expanded_groups.value);
    return;
  }

  // Expand the group
  expanded_groups.value.add(key);
  expanded_groups.value = new Set(expanded_groups.value);

  // Check if we need to fetch definitions
  const missing_ids = group.puzzles
    .map(p => p.puzzle_id)
    .filter(id => !puzzle_definitions.value.has(id));

  if (missing_ids.length > 0) {
    loading_groups.value.add(key);
    loading_groups.value = new Set(loading_groups.value);

    // Fetch missing definitions in parallel
    await Promise.all(missing_ids.map(id => fetch_puzzle_definition(id)));

    loading_groups.value.delete(key);
    loading_groups.value = new Set(loading_groups.value);
  }
};

// Get puzzle definition from cache
const get_definition = (puzzle_id: string): PuzzleDefinition | undefined => {
  return puzzle_definitions.value.get(puzzle_id);
};

// Create puzzle state for rendering
const get_puzzle_state = (puzzle_id: string) => {
  const def = get_definition(puzzle_id);
  if (!def) return null;
  return {
    definition: def,
    board: (def as any).solution || def.initial_state,
  };
};

const handle_download_group = async (group: PriorityGroup) => {
  const url = get_priority_group_export_url(
    group.puzzle_type,
    group.puzzle_size,
    group.puzzle_difficulty,
    true
  );
  const difficulty_part = group.puzzle_difficulty ? `_${group.puzzle_difficulty}` : "";
  const filename = `priority_${group.puzzle_type}_${group.puzzle_size}${difficulty_part}_attempts.json`;
  await download_blob(url, filename);
};

const handle_add = async () => {
  if (!new_puzzle_id.value.trim()) {
    add_error.value = "Please enter a puzzle ID";
    return;
  }

  try {
    adding.value = true;
    add_error.value = null;
    await add_priority_puzzle(new_puzzle_id.value.trim());
    add_dialog_open.value = false;
    new_puzzle_id.value = "";
    await fetch_priorities();
  } catch (err: any) {
    add_error.value = err.response?.data?.detail || "Failed to add puzzle to priority";
    console.error("Error adding priority puzzle:", err);
  } finally {
    adding.value = false;
  }
};

const fetch_priorities = async () => {
  try {
    loading.value = true;
    error.value = null;

    // Fetch grouped summary data only (no definitions)
    const response = await get_priority_puzzles_grouped(false);
    groups.value = response.data.groups;
    total_groups.value = response.data.total_groups;
    total_puzzles.value = response.data.total_puzzles;
  } catch (err) {
    error.value = "Failed to load priority puzzles";
    console.error("Error fetching priority puzzles:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetch_priorities();
});
</script>

<template>
  <div class="flex flex-col gap-4 w-full items-center p-4">
    <Container class="max-w-6xl w-full">
      <div class="flex items-center justify-between mb-4">
        <div class="text-2xl font-semibold">Priority Puzzles</div>
        <Button @click="add_dialog_open = true">
          <Plus class="h-4 w-4 mr-2" />
          Add Puzzle
        </Button>
      </div>
      <p class="text-muted-foreground text-sm mb-4">
        Priority puzzles are served first to users who haven't seen them. Click a group to expand and view puzzles.
      </p>
    </Container>

    <Container class="max-w-6xl w-full">
      <!-- Summary -->
      <div class="flex items-center justify-end mb-4">
        <div class="text-sm text-muted-foreground">
          {{ total_groups }} group(s) · {{ total_puzzles }} puzzle(s)
        </div>
      </div>

      <div v-if="loading" class="text-muted-foreground text-center py-8">Loading...</div>
      <div v-else-if="error" class="text-red-500 text-center py-8">{{ error }}</div>
      <div v-else-if="groups.length === 0" class="text-muted-foreground text-center py-8">
        No priority puzzles found. Click "Add Puzzle" to get started.
      </div>

      <!-- Groups -->
      <div v-else class="space-y-2">
        <Container
          v-for="group in sorted_groups"
          :key="get_group_key(group)"
        >
          <!-- Group Header (always visible) -->
          <div
            class="flex items-center justify-between cursor-pointer"
            @click="is_known_puzzle_type(group.puzzle_type) ? toggle_group(group) : null"
          >
            <div class="flex items-center gap-2">
              <!-- Expand/collapse icon for known types -->
              <template v-if="is_known_puzzle_type(group.puzzle_type)">
                <ChevronDown v-if="is_group_expanded(group)" class="h-4 w-4 text-muted-foreground" />
                <ChevronRight v-else class="h-4 w-4 text-muted-foreground" />
              </template>

              <!-- Unknown type badge -->
              <Badge v-if="!is_known_puzzle_type(group.puzzle_type)" variant="secondary">
                Unknown: {{ group.puzzle_type }}
              </Badge>
              <span v-else class="font-semibold">{{ format_group_title(group) }}</span>

              <span class="text-sm text-muted-foreground">
                {{ group.total_puzzles }} puzzle(s) ·
                {{ group.total_shown }} shown ·
                {{ group.total_solved }} solved
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              @click.stop="handle_download_group(group)"
              :disabled="group.total_solved === 0"
              :title="group.total_solved === 0 ? 'No solved attempts to download' : 'Download all solved attempts for this group'"
            >
              <Download class="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>

          <!-- Expanded Content (puzzle grid) -->
          <div
            v-if="is_known_puzzle_type(group.puzzle_type) && is_group_expanded(group)"
            class="mt-2 pt-2 border-t"
          >
            <!-- Loading state -->
            <div v-if="is_group_loading(group)" class="text-sm text-muted-foreground text-center py-4">
              Loading puzzles...
            </div>

            <!-- Puzzle Grid -->
            <div v-else class="grid grid-cols-4 md:grid-cols-6 gap-2">
              <div
                v-for="puzzle in group.puzzles"
                :key="puzzle.id"
              >
                <div
                  class="overflow-hidden border rounded-sm bg-white aspect-square"
                  :class="{ 'opacity-50': !puzzle.is_active }"
                >
                  <div class="@container aspect-square box-border place-items-center grid select-none pointer-events-none overflow-hidden p-0.5">
                    <PuzzleRenderer
                      v-if="get_definition(puzzle.puzzle_id)"
                      :definition="get_definition(puzzle.puzzle_id)!"
                      :state="get_puzzle_state(puzzle.puzzle_id)"
                    />
                    <div v-else class="text-xs text-gray-400">...</div>
                  </div>
                </div>
                <!-- Stats below puzzle -->
                <div class="text-xs text-center mt-1">
                  {{ puzzle.times_shown }} shown - {{ puzzle.times_solved }} solved
                </div>
              </div>
            </div>
          </div>
        </Container>
      </div>
    </Container>

    <!-- Add Puzzle Dialog -->
    <Dialog v-model:open="add_dialog_open">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>Add Priority Puzzle</DialogTitle>
          <DialogDescription>
            Enter the UUID of the puzzle you want to add to the priority queue.
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-4">
          <div class="space-y-2">
            <Label for="puzzle-id">Puzzle ID</Label>
            <Input
              id="puzzle-id"
              v-model="new_puzzle_id"
              placeholder="e.g., 01234567-89ab-cdef-0123-456789abcdef"
              @keyup.enter="handle_add"
            />
          </div>
          <div v-if="add_error" class="text-red-500 text-sm">
            {{ add_error }}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="add_dialog_open = false">Cancel</Button>
          <Button @click="handle_add" :disabled="adding">
            {{ adding ? "Adding..." : "Add to Priority" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

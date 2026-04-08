<script setup lang="ts">
/**
 * PuzzleChallenge — play a specific puzzle by ID.
 * Used for shareable puzzle links: /puzzle/:puzzle_id?by=username&time=30
 */
import { ref, provide, defineAsyncComponent } from "vue";
import { useRoute } from "vue-router";
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";
import { api } from "@/core/services/client";

const route = useRoute();
const puzzle_id = route.params.puzzle_id as string;

provide("challenge-puzzle-id", puzzle_id);

// Fetch puzzle type during setup (top-level await in <script setup>)
const error = ref<string | null>(null);
let game_component: any = null;

try {
  const { data, error: fetchError } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
    params: { path: { puzzle_id } },
  });
  if (fetchError || !data) {
    error.value = "Puzzle not found.";
  } else {
    const puzzle_type = (data as any).puzzle_type;
    const game_entry = ACTIVE_GAMES[puzzle_type];
    if (!game_entry) {
      error.value = `Unknown puzzle type: ${puzzle_type}`;
    } else {
      game_component = defineAsyncComponent(game_entry.freeplay);
    }
  }
} catch {
  error.value = "Failed to load puzzle.";
}

</script>

<template>
  <Container v-if="error" class="text-center py-20">
    <p class="text-gray-500">{{ error }}</p>
  </Container>
  <Suspense v-else-if="game_component">
    <component :is="game_component" />
  </Suspense>
</template>

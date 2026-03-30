<script setup lang="ts">
/** dedicated leaderboard page — multi-column view across puzzle types */
import { ref, reactive, computed, watch, onMounted } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore";
import PlaybackTimeline from "@/features/playback/components/PlaybackTimeline.vue";
import { usePlaybackControls } from "@/features/playback/composables/usePlaybackControls";
import type { LeaderboardEntry, PuzzleVariant, PlaybackFrame } from "@/core/types";

const metadata_store = usePuzzleMetadataStore();
const puzzle_types = Object.keys(ACTIVE_GAMES);

// per-type state
const selected = reactive<Record<string, { size: string; difficulty: string | null; period: string; method: string }>>({});
const leaderboards = ref<Record<string, LeaderboardEntry[]>>({});
const loading = ref<Record<string, boolean>>({});

for (const pt of puzzle_types) {
  const variants = metadata_store.getVariants(pt);
  const v = variants.length > 0 ? variants[0] : { size: "", difficulty: null };
  selected[pt] = { size: v.size, difficulty: v.difficulty ?? null, period: "all_time", method: "best" };
}

// -- preview playback state --
interface PreviewState {
  attempt_id: string | null;
  frames: PlaybackFrame[];
  definition: any;
  controls: ReturnType<typeof usePlaybackControls>;
}

// pre-create controls during setup for each puzzle type
const preview_frames: Record<string, PlaybackFrame[]> = {};
const preview_controls: Record<string, ReturnType<typeof usePlaybackControls>> = {};
for (const pt of puzzle_types) {
  preview_frames[pt] = [];
  preview_controls[pt] = usePlaybackControls(() => preview_frames[pt].length);
}

const previews = ref<Record<string, { attempt_id: string | null; frames: PlaybackFrame[]; definition: any }>>({});

async function load_preview(puzzle_type: string, attempt_id: string) {
  try {
    const res = await fetch(`/api/puzzle/freeplay/attempts/${attempt_id}`, { credentials: "include" });
    if (!res.ok) return;
    const data = await res.json();
    preview_frames[puzzle_type] = data.frames;
    preview_controls[puzzle_type].seek(0);
    previews.value = {
      ...previews.value,
      [puzzle_type]: { attempt_id, frames: data.frames, definition: data.puzzle_definition },
    };
  } catch {
    // skip
  }
}

function get_canvas_state(pt: string) {
  const p = previews.value[pt];
  if (!p?.frames?.length) return null;
  const idx = Math.min(preview_controls[pt].current_frame.value, p.frames.length - 1);
  const frame = p.frames[idx];
  return frame ? { definition: p.definition, board: frame.board, violations: [], solved: false } : null;
}

function select_entry(pt: string, entry: LeaderboardEntry) {
  if (entry.attempt_id) {
    load_preview(pt, entry.attempt_id);
  }
}

// -- leaderboard fetching --
async function fetch_leaderboard(puzzle_type: string) {
  const s = selected[puzzle_type];
  if (!s?.size) return;

  loading.value = { ...loading.value, [puzzle_type]: true };
  try {
    const params = new URLSearchParams({
      puzzle_type,
      puzzle_size: s.size,
      puzzle_difficulty: s.difficulty ?? "",
      limit: "10",
      time_period: s.period,
      scoring_method: s.method,
    });
    const res = await fetch(`/api/puzzle/freeplay/leaderboard?${params}`, { credentials: "include" });
    if (res.ok) {
      const data = await res.json();
      const entries = data.leaderboard ?? [];
      leaderboards.value = { ...leaderboards.value, [puzzle_type]: entries };
      // auto-load #1's preview
      const top = entries.find((e: LeaderboardEntry) => e.attempt_id);
      if (top?.attempt_id) {
        load_preview(puzzle_type, top.attempt_id);
      }
    }
  } catch {
    // keep existing data
  } finally {
    loading.value = { ...loading.value, [puzzle_type]: false };
  }
}

async function fetch_all() {
  await Promise.all(puzzle_types.map(fetch_leaderboard));
}

onMounted(fetch_all);

function get_game_icon(puzzle_type: string): string {
  return ACTIVE_GAMES[puzzle_type]?.icon ?? "🧩";
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function get_variant_label(v: PuzzleVariant): string {
  if (v.difficulty) return `${v.size} ${capitalize(v.difficulty)}`;
  return v.size;
}

function variant_key(v: { size: string; difficulty?: string | null }): string {
  return `${v.size}|${v.difficulty ?? ""}`;
}

function on_variant_change(pt: string, key: string) {
  const variant = metadata_store.getVariants(pt).find(v => variant_key(v) === key);
  if (variant) {
    selected[pt].size = variant.size;
    selected[pt].difficulty = variant.difficulty ?? null;
    fetch_leaderboard(pt);
  }
}

function on_period_change(pt: string, val: string) {
  selected[pt].period = val;
  fetch_leaderboard(pt);
}

function on_method_change(pt: string, val: string) {
  selected[pt].method = val;
  fetch_leaderboard(pt);
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <!-- header -->
    <Container>
      <h1 class="text-2xl font-bold">Leaderboard</h1>
    </Container>

    <!-- leaderboard columns -->
    <div class="grid grid-cols-4 gap-2">
      <Container v-for="pt in puzzle_types" :key="pt" class="flex flex-col">
        <!-- type header -->
        <div class="flex items-center gap-1.5 mb-1">
          <span>{{ get_game_icon(pt) }}</span>
          <span class="text-sm font-semibold uppercase tracking-wide">{{ capitalize(pt) }}</span>
        </div>

        <!-- per-type selectors -->
        <div class="flex flex-wrap gap-1 mb-2">
          <select
            class="text-[10px] text-gray-500 border border-gray-200 rounded px-1 py-0.5 bg-white cursor-pointer"
            :value="variant_key(selected[pt])"
            @change="on_variant_change(pt, ($event.target as HTMLSelectElement).value)"
          >
            <option
              v-for="v in metadata_store.getVariants(pt)"
              :key="variant_key(v)"
              :value="variant_key(v)"
            >
              {{ get_variant_label(v) }}
            </option>
          </select>
          <select
            class="text-[10px] text-gray-500 border border-gray-200 rounded px-1 py-0.5 bg-white cursor-pointer"
            :value="selected[pt].period"
            @change="on_period_change(pt, ($event.target as HTMLSelectElement).value)"
          >
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="all_time">All Time</option>
          </select>
          <select
            class="text-[10px] text-gray-500 border border-gray-200 rounded px-1 py-0.5 bg-white cursor-pointer"
            :value="selected[pt].method"
            @change="on_method_change(pt, ($event.target as HTMLSelectElement).value)"
          >
            <option value="best">Best</option>
            <option value="ao_n">Ao3</option>
          </select>
        </div>

        <!-- preview: board + timeline -->
        <div v-if="previews[pt]?.frames?.length" class="mb-2">
          <div class="w-full overflow-hidden pointer-events-none select-none">
            <component
              v-if="ACTIVE_GAMES[pt]?.component && get_canvas_state(pt)"
              :is="ACTIVE_GAMES[pt].component"
              :state="get_canvas_state(pt)"
            />
          </div>
          <PlaybackTimeline
            :frames="previews[pt].frames"
            :current_frame="preview_controls[pt].current_frame.value"
            :is_playing="preview_controls[pt].is_playing.value"
            :moves_per_second="preview_controls[pt].moves_per_second.value"
            size="small"
            @seek="preview_controls[pt].seek"
            @toggle-play="preview_controls[pt].toggle_play"
            @set-mps="preview_controls[pt].set_mps"
          />
        </div>

        <!-- loading -->
        <div v-if="loading[pt]" class="text-center text-gray-400 text-xs py-4">loading...</div>

        <!-- empty -->
        <div v-else-if="!leaderboards[pt]?.length" class="text-center text-gray-400 text-xs py-4">no entries</div>

        <!-- entries -->
        <div v-else class="flex flex-col">
          <div
            v-for="entry in leaderboards[pt]"
            :key="entry.rank"
            class="flex items-center justify-between py-1 text-sm border-b border-gray-100 last:border-0"
            :class="{
              'font-bold': entry.is_current_user,
              'bg-blue-50': entry.attempt_id === previews[pt]?.attempt_id,
            }"
          >
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-gray-400 text-xs w-4 text-right shrink-0">{{ entry.rank }}</span>
              <router-link
                :to="{ name: 'user-profile', params: { username: entry.username } }"
                class="truncate hover:underline"
              >
                {{ entry.username }}
              </router-link>
            </div>
            <span
              class="text-xs shrink-0 ml-2"
              :class="entry.attempt_id ? 'text-blue-500 cursor-pointer hover:underline' : 'text-gray-500'"
              @click="select_entry(pt, entry)"
            >
              {{ entry.duration_display }}
            </span>
          </div>
        </div>
      </Container>
    </div>
  </div>
</template>

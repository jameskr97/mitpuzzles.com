<script setup lang="ts">
/** public user profile page — fetches stats and renders sub-components */
import { ref, shallowRef, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";
import type { PlaybackFrame } from "@/core/types";
import { usePlaybackControls } from "@/features/playback/composables/usePlaybackControls";

import ProfileHeader from "@/features/profile/ProfileHeader.vue";
import ProfileSolveChart from "@/features/profile/ProfileSolveChart.vue";
import ProfileSidebar from "@/features/profile/ProfileSidebar.vue";
import ProfileFeaturedSolve from "@/features/profile/ProfileFeaturedSolve.vue";
import ProfileGameLog from "@/features/profile/ProfileGameLog.vue";
import ProfileActivityFeed from "@/features/profile/ProfileActivityFeed.vue";

const route = useRoute();
const username = route.params.username as string;

// -- state --
const loading = ref(true);
const error = ref<string | null>(null);

const stats = ref({
  username,
  member_since: "",
  is_own_profile: false,
  total_puzzles_solved: 0,
  total_puzzles_attempted: 0,
  total_time_seconds: 0,
  puzzle_type_stats: [] as {
    puzzle_type: string;
    solved_count: number;
    attempt_count: number;
    best_time: number | null;
    avg_time: number | null;
  }[],
  daily_streak: { current_streak: 0, longest_streak: 0, total_dailies_solved: 0, fastest_daily_count: 0 },
});

const solve_time_history = ref<Record<string, { date: string; avg_time: number }[]>>({});
const activity_feed = ref<{ date: string; entries: { icon: string; text: string; detail?: string }[] }[]>([]);

interface GameLogEntry {
  puzzle_type: string;
  puzzle_size: string;
  puzzle_difficulty: string | null;
  time: number | null;
  solved: boolean;
  date: string;
  attempt_id: string;
}

const game_log = ref<GameLogEntry[]>([]);

const solve_rate = computed(() => {
  if (stats.value.total_puzzles_attempted === 0) return 0;
  return Math.round((stats.value.total_puzzles_solved / stats.value.total_puzzles_attempted) * 100);
});

// -- featured solves (pre-create 2 playback control slots during setup) --
interface FeaturedGame {
  puzzle_type: string;
  best_time: number;
  frames: PlaybackFrame[];
  canvas_component: any;
  canvas_state: any;
  controls: ReturnType<typeof usePlaybackControls>;
}

const featured_frames: PlaybackFrame[][] = [[], []];
const featured_controls = [
  usePlaybackControls(() => featured_frames[0].length),
  usePlaybackControls(() => featured_frames[1].length),
];
const featured_games = shallowRef<FeaturedGame[]>([]);

async function load_featured_solve(index: number, attempt_id: string, puzzle_type: string, best_time: number) {
  try {
    const res = await fetch(`/api/puzzle/freeplay/attempts/${attempt_id}`, { credentials: "include" });
    if (!res.ok) return;
    const data = await res.json();
    const frames: PlaybackFrame[] = data.frames;
    featured_frames[index] = frames;
    const controls = featured_controls[index];
    const canvas_component = ACTIVE_GAMES[data.puzzle_definition?.puzzle_type]?.component ?? null;
    featured_games.value = [
      ...featured_games.value,
      {
        puzzle_type,
        best_time,
        frames,
        canvas_component,
        canvas_state: computed(() => {
          const frame = frames[Math.min(controls.current_frame.value, frames.length - 1)];
          return frame
            ? { definition: data.puzzle_definition, board: frame.board, violations: [], solved: false }
            : null;
        }),
        controls,
      },
    ];
  } catch {
    // skip failed loads
  }
}

// -- fetch --
onMounted(async () => {
  try {
    const res = await fetch(`/api/users/${username}/stats`, { credentials: "include" });
    if (!res.ok) {
      error.value = res.status === 404 ? "user not found" : "failed to load profile";
      return;
    }
    const data = await res.json();

    stats.value = {
      username: data.username,
      member_since: data.member_since,
      is_own_profile: data.is_own_profile,
      total_puzzles_solved: data.total_puzzles_solved,
      total_puzzles_attempted: data.total_puzzles_attempted,
      total_time_seconds: data.total_time_seconds,
      puzzle_type_stats: data.puzzle_type_stats,
      daily_streak: data.daily_streak,
    };

    const history: Record<string, { date: string; avg_time: number }[]> = {};
    for (const series of data.solve_time_history) {
      history[series.puzzle_type] = series.data;
    }
    solve_time_history.value = history;

    activity_feed.value = data.activity_feed;
    game_log.value = data.game_log;

    for (let i = 0; i < Math.min(data.featured_solves.length, 2); i++) {
      const featured = data.featured_solves[i];
      await load_featured_solve(i, featured.attempt_id, featured.puzzle_type, featured.best_time);
    }
  } catch (e) {
    error.value = "failed to load profile";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <!-- loading -->
  <Container v-if="loading" class="flex justify-center py-20">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
  </Container>

  <!-- error -->
  <Container v-else-if="error" class="text-center py-20">
    <p class="text-gray-500">{{ error }}</p>
  </Container>

  <div v-else class="flex flex-col gap-2">
    <!-- row 1: header + stats -->
    <ProfileHeader
      :username="stats.username"
      :is_own_profile="stats.is_own_profile"
      :total_puzzles_solved="stats.total_puzzles_solved"
      :total_puzzles_attempted="stats.total_puzzles_attempted"
      :solve_rate="solve_rate"
      :current_streak="stats.daily_streak.current_streak"
      :fastest_daily_count="stats.daily_streak.fastest_daily_count"
      :puzzle_type_stats="stats.puzzle_type_stats"
    />

    <!-- row 2: chart + sidebar -->
    <div class="grid grid-cols-[4fr_1fr] gap-2">
      <ProfileSolveChart :solve_time_history="solve_time_history" />
      <ProfileSidebar
        :member_since="stats.member_since"
        :total_time_seconds="stats.total_time_seconds"
        :daily_streak="stats.daily_streak"
      />
    </div>

    <!-- row 3: featured + recent games | activity -->
    <div class="grid grid-cols-[2fr_1fr] gap-2 grid-rows-1">
      <div class="grid grid-cols-2 gap-2 min-h-0">
        <ProfileFeaturedSolve
          v-for="featured in featured_games"
          :key="featured.puzzle_type"
          :puzzle_type="featured.puzzle_type"
          :best_time="featured.best_time"
          :frames="featured.frames"
          :canvas_component="featured.canvas_component"
          :canvas_state="featured.canvas_state"
          :controls="featured.controls"
        />
        <ProfileGameLog :games="game_log" class="col-span-2" />
      </div>
      <ProfileActivityFeed :activity="activity_feed" class="overflow-hidden h-0 min-h-full" />
    </div>
  </div>
</template>

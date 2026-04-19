<script setup lang="ts">
/** user statistics page — own profile only */
import { ref, computed, onMounted } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { useAuthStore } from "@/core/store/useAuthStore";

import ProfileHeader from "@/features/profile/ProfileHeader.vue";
import ProfileSolveChart from "@/features/profile/ProfileSolveChart.vue";
import ProfileStats from "@/features/profile/ProfileStats.vue";
import ProfileSidebar from "@/features/profile/ProfileSidebar.vue";

const auth = useAuthStore();
const username = auth.user?.username ?? "";

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

const solve_rate = computed(() => {
  if (stats.value.total_puzzles_attempted === 0) return 0;
  return Math.round((stats.value.total_puzzles_solved / stats.value.total_puzzles_attempted) * 100);
});

// -- fetch --
onMounted(async () => {
  try {
    const res = await fetch("/api/me/stats", { credentials: "include" });
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
    <!-- row 1: header -->
    <ProfileHeader
      :username="stats.username"
      :is_own_profile="stats.is_own_profile"
    />

    <!-- row 2: chart + stats + sidebar -->
    <div class="grid grid-cols-1 md:grid-cols-[3fr_1fr_1fr] gap-2">
      <ProfileSolveChart :solve_time_history="solve_time_history" />
      <ProfileStats
        :total_puzzles_solved="stats.total_puzzles_solved"
        :total_puzzles_attempted="stats.total_puzzles_attempted"
        :solve_rate="solve_rate"
        :current_streak="stats.daily_streak.current_streak"
        :puzzle_type_stats="stats.puzzle_type_stats"
      />
      <ProfileSidebar
        :member_since="stats.member_since"
        :total_time_seconds="stats.total_time_seconds"
        :daily_streak="stats.daily_streak"
      />
    </div>

  </div>
</template>

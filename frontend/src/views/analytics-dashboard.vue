<script setup lang="ts">
import Container from "@/components/ui/Container.vue";
import { Status, StatusIndicator, StatusLabel } from "@/components/ui/indicator";
import { ref, onMounted, watch, computed } from 'vue';
import {
  get_analytics_stats_summary,
  get_analytics_game_statistics,
  get_analytics_user_engagement,
  get_analytics_game_types_breakdown,
  get_analytics_registrations_over_time,
  type StatsData
} from '@/services/app';

const stats = ref<StatsData | null>(null);
const game_stats = ref<any>(null);
const user_engagement = ref<any>(null);
const game_breakdown = ref<any>(null);
const registrations = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

// Filter state
const include_superusers = ref(false);
const selected_user_type = ref<'all' | 'logged_in' | 'anonymous'>('all');
const selected_game_types = ref<Set<string>>(new Set());
const selected_game_sizes = ref<Set<string>>(new Set());
const selected_difficulties = ref<Set<string>>(new Set());
const start_date = ref('');
const end_date = ref('');

// Available filter options (will be populated from API)
const filter_options = ref({
  game_types: ['minesweeper', 'sudoku', 'tents', 'battleship'] as string[],
  game_sizes: ['5x5', '9x9', '10x10', '15x15'] as string[],
  difficulties: ['easy', 'medium', 'hard'] as string[]
});

// Computed values for selected counts
const selected_types_count = computed(() => selected_game_types.value.size);
const selected_sizes_count = computed(() => selected_game_sizes.value.size);
const selected_difficulties_count = computed(() => selected_difficulties.value.size);

// Toggle functions
const toggle_game_type = (type: string) => {
  if (selected_game_types.value.has(type)) {
    selected_game_types.value.delete(type);
  } else {
    selected_game_types.value.add(type);
  }
};

const toggle_game_size = (size: string) => {
  if (selected_game_sizes.value.has(size)) {
    selected_game_sizes.value.delete(size);
  } else {
    selected_game_sizes.value.add(size);
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
  selected_user_type.value = 'all';
  selected_game_types.value.clear();
  selected_game_sizes.value.clear();
  selected_difficulties.value.clear();
  start_date.value = '';
  end_date.value = '';
};

const fetch_all_data = async () => {
  try {
    loading.value = true;

    // Fetch all analytics data in parallel
    const [
      statsResponse,
      gameStatsResponse,
      engagementResponse,
      breakdownResponse,
      registrationsResponse
    ] = await Promise.all([
      get_analytics_stats_summary(include_superusers.value),
      get_analytics_game_statistics({
        include_superusers: include_superusers.value,
        user_filter: selected_user_type.value,
        game_type: selected_game_types.value.size > 0 ? Array.from(selected_game_types.value) : undefined,
        game_size: selected_game_sizes.value.size > 0 ? Array.from(selected_game_sizes.value) : undefined,
        difficulty: selected_difficulties.value.size > 0 ? Array.from(selected_difficulties.value) : undefined,
        start_date: start_date.value || undefined,
        end_date: end_date.value || undefined
      }),
      get_analytics_user_engagement({
        include_superusers: include_superusers.value,
        start_date: start_date.value || undefined,
        end_date: end_date.value || undefined
      }),
      get_analytics_game_types_breakdown({
        include_superusers: include_superusers.value,
        user_filter: selected_user_type.value,
        start_date: start_date.value || undefined,
        end_date: end_date.value || undefined
      }),
      get_analytics_registrations_over_time({
        start_date: start_date.value || undefined,
        end_date: end_date.value || undefined
      })
    ]);

    stats.value = statsResponse.data;
    game_stats.value = gameStatsResponse.data;
    user_engagement.value = engagementResponse.data;
    game_breakdown.value = breakdownResponse.data;
    registrations.value = registrationsResponse.data;

  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch analytics data';
    console.error('Error fetching analytics:', err);
  } finally {
    loading.value = false;
  }
};

const get_chart_data_for_games_per_day = () => {
  if (!game_stats.value?.data) return [];
  return game_stats.value.data.slice(-7);
};

const get_chart_data_for_user_distribution = () => {
  if (!user_engagement.value?.games_played_distribution) return [];
  const dist = user_engagement.value.games_played_distribution;
  return [
    { label: '1 Game', value: dist.users_played_1_game || 0 },
    { label: '2-5 Games', value: dist.users_played_2_to_5_games || 0 },
    { label: '10+ Games', value: dist.users_played_10_plus_games || 0 }
  ];
};

const get_chart_data_for_game_types = () => {
  if (!game_breakdown.value?.data) return [];

  // Group by puzzle_type and sum games_played
  const typeGroups: Record<string, number> = {};
  game_breakdown.value.data.forEach((item: any) => {
    typeGroups[item.puzzle_type] = (typeGroups[item.puzzle_type] || 0) + item.games_played;
  });

  return Object.entries(typeGroups).map(([type, count]) => ({
    label: type,
    value: count
  }));
};

const get_max_value = (data: any[]) => {
  return Math.max(...data.map(d => d.value || d.total_games || 0));
};

// Watch for filter changes and refetch data
watch([
  include_superusers,
  selected_user_type,
  selected_game_types,
  selected_game_sizes,
  selected_difficulties,
  start_date,
  end_date
], () => {
  fetch_all_data();
}, { deep: true });

onMounted(() => {
  fetch_all_data();
});

</script>

<template>
  <div class="flex h-full">
    <!-- Left Sidebar -->
    <Container class="w-1/5 min-w-[250px] my-2 p-2 overflow-y-auto">
      <h2 class="text-lg font-semibold text-center mb-4">Analytics Filters</h2>

      <!-- Include Superusers -->
      <div class="space-y-1 mb-4">
        <h3 class="text-sm font-medium text-gray-700">Options</h3>
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <div class="relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50">
            <div class="flex items-center justify-center w-3 h-3 mr-2">
              <input
                v-model="include_superusers"
                type="checkbox"
                class="h-3 w-3 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            <span class="flex-1 text-xs font-medium text-gray-900">
              Include superusers
            </span>
          </div>
        </div>
      </div>

      <!-- User Type Filter -->
      <div class="space-y-1 mb-4">
        <h3 class="text-sm font-medium text-gray-700">User Type</h3>
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <div
            v-for="userType in [
              { value: 'all', label: 'All Users' },
              { value: 'logged_in', label: 'Logged In' },
              { value: 'anonymous', label: 'Anonymous' }
            ]"
            :key="userType.value"
            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
            :class="{ 'bg-blue-50 border-blue-200': selected_user_type === userType.value }"
            @click="selected_user_type = userType.value"
          >
            <div class="flex items-center justify-center w-3 h-3 mr-2">
              <div
                v-if="selected_user_type === userType.value"
                class="w-2 h-2 bg-blue-600 rounded-full"
              ></div>
            </div>
            <span class="flex-1 text-xs font-medium text-gray-900">
              {{ userType.label }}
            </span>
          </div>
        </div>
      </div>

      <!-- Date Range -->
      <div class="space-y-1 mb-4">
        <h3 class="text-sm font-medium text-gray-700">Date Range</h3>
        <div class="space-y-2">
          <div>
            <label class="block text-xs text-gray-600 mb-1">Start Date</label>
            <input v-model="start_date" type="date" class="w-full px-2 py-1 text-xs border border-gray-300 rounded">
          </div>
          <div>
            <label class="block text-xs text-gray-600 mb-1">End Date</label>
            <input v-model="end_date" type="date" class="w-full px-2 py-1 text-xs border border-gray-300 rounded">
          </div>
        </div>
      </div>

<!--      &lt;!&ndash; Game Type Filters &ndash;&gt;-->
<!--      <div class="space-y-1 mb-4">-->
<!--        <div class="flex items-center justify-between">-->
<!--          <h3 class="text-sm font-medium text-gray-700">Game Types</h3>-->
<!--          <span v-if="selected_types_count > 0" class="text-xs text-blue-600 font-medium">-->
<!--            {{ selected_types_count }} selected-->
<!--          </span>-->
<!--        </div>-->
<!--        <div class="border border-gray-200 rounded-lg overflow-hidden">-->
<!--          <div-->
<!--            v-for="gameType in filter_options.game_types"-->
<!--            :key="gameType"-->
<!--            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"-->
<!--            :class="{ 'bg-blue-50 border-blue-200': selected_game_types.has(gameType) }"-->
<!--            @click="toggle_game_type(gameType)"-->
<!--          >-->
<!--            <div class="flex items-center justify-center w-3 h-3 mr-2">-->
<!--              <svg-->
<!--                v-if="selected_game_types.has(gameType)"-->
<!--                class="w-2.5 h-2.5 text-blue-600"-->
<!--                fill="currentColor"-->
<!--                viewBox="0 0 20 20"-->
<!--              >-->
<!--                <path-->
<!--                  fill-rule="evenodd"-->
<!--                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"-->
<!--                  clip-rule="evenodd"-->
<!--                />-->
<!--              </svg>-->
<!--            </div>-->
<!--            <span class="flex-1 text-xs font-medium text-gray-900 capitalize">-->
<!--              {{ gameType }}-->
<!--            </span>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->

<!--      &lt;!&ndash; Game Size Filters &ndash;&gt;-->
<!--      <div class="space-y-1 mb-4">-->
<!--        <div class="flex items-center justify-between">-->
<!--          <h3 class="text-sm font-medium text-gray-700">Game Sizes</h3>-->
<!--          <span v-if="selected_sizes_count > 0" class="text-xs text-blue-600 font-medium">-->
<!--            {{ selected_sizes_count }} selected-->
<!--          </span>-->
<!--        </div>-->
<!--        <div class="border border-gray-200 rounded-lg overflow-hidden">-->
<!--          <div-->
<!--            v-for="gameSize in filter_options.game_sizes"-->
<!--            :key="gameSize"-->
<!--            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"-->
<!--            :class="{ 'bg-blue-50 border-blue-200': selected_game_sizes.has(gameSize) }"-->
<!--            @click="toggle_game_size(gameSize)"-->
<!--          >-->
<!--            <div class="flex items-center justify-center w-3 h-3 mr-2">-->
<!--              <svg-->
<!--                v-if="selected_game_sizes.has(gameSize)"-->
<!--                class="w-2.5 h-2.5 text-blue-600"-->
<!--                fill="currentColor"-->
<!--                viewBox="0 0 20 20"-->
<!--              >-->
<!--                <path-->
<!--                  fill-rule="evenodd"-->
<!--                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"-->
<!--                  clip-rule="evenodd"-->
<!--                />-->
<!--              </svg>-->
<!--            </div>-->
<!--            <span class="flex-1 text-xs font-medium text-gray-900">-->
<!--              {{ gameSize }}-->
<!--            </span>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->

<!--      &lt;!&ndash; Difficulty Filters &ndash;&gt;-->
<!--      <div class="space-y-1 mb-4">-->
<!--        <div class="flex items-center justify-between">-->
<!--          <h3 class="text-sm font-medium text-gray-700">Difficulty</h3>-->
<!--          <span v-if="selected_difficulties_count > 0" class="text-xs text-blue-600 font-medium">-->
<!--            {{ selected_difficulties_count }} selected-->
<!--          </span>-->
<!--        </div>-->
<!--        <div class="border border-gray-200 rounded-lg overflow-hidden">-->
<!--          <div-->
<!--            v-for="difficulty in filter_options.difficulties"-->
<!--            :key="difficulty"-->
<!--            class="listbox-item relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"-->
<!--            :class="{ 'bg-blue-50 border-blue-200': selected_difficulties.has(difficulty) }"-->
<!--            @click="toggle_difficulty(difficulty)"-->
<!--          >-->
<!--            <div class="flex items-center justify-center w-3 h-3 mr-2">-->
<!--              <svg-->
<!--                v-if="selected_difficulties.has(difficulty)"-->
<!--                class="w-2.5 h-2.5 text-blue-600"-->
<!--                fill="currentColor"-->
<!--                viewBox="0 0 20 20"-->
<!--              >-->
<!--                <path-->
<!--                  fill-rule="evenodd"-->
<!--                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"-->
<!--                  clip-rule="evenodd"-->
<!--                />-->
<!--              </svg>-->
<!--            </div>-->
<!--            <span class="flex-1 text-xs font-medium text-gray-900 capitalize">-->
<!--              {{ difficulty }}-->
<!--            </span>-->
<!--          </div>-->
<!--        </div>-->
<!--      </div>-->

      <!-- Clear Filters Button -->
      <button
        @click="clear_all_filters"
        class="w-full px-3 py-2 text-xs bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
      >
        Clear All Filters
      </button>
    </Container>

    <!-- Main Content Area -->
    <div class="flex flex-col gap-2 m-2 w-full">
      <!-- Stats Cards -->
      <div class="flex flex-row gap-2 w-full justify-evenly">
        <div v-if="loading" class="w-full text-center">Loading...</div>
        <div v-else-if="error" class="w-full text-center text-red-500">Error: {{ error }}</div>
        <template v-else-if="stats">
          <Container class="w-full">
            <div class="text-center font-bold underline">Total Users</div>
            <div class="text-center text-2xl">{{ stats.total_users }}</div>
          </Container>
          <Container class="w-full">
            <div class="text-center font-bold underline">Active Today</div>
            <div class="text-center text-2xl">{{ stats.active_users_today }}</div>
          </Container>
          <Container class="w-full">
            <div class="text-center font-bold underline">Total Games</div>
            <div class="text-center text-2xl">{{ stats.total_games_played }}</div>
          </Container>
          <Container class="w-full">
            <div class="text-center font-bold underline">Avg Session</div>
            <div class="text-center text-2xl">{{ stats.avg_session_duration_minutes }}m</div>
          </Container>
        </template>
      </div>

    <!-- Charts Section -->
    <div v-if="!loading && !error" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Games Per Day Chart -->
      <Container class="p-4">
        <h3 class="text-lg font-bold mb-4">Games Per Day</h3>
        <div class="h-64">
          <div v-if="get_chart_data_for_games_per_day().length === 0" class="h-full flex items-center justify-center bg-gray-100 rounded">
            <span class="text-gray-500">No data available</span>
          </div>
          <div v-else class="h-full flex items-end justify-around bg-gray-50 rounded p-4">
            <div
              v-for="day in get_chart_data_for_games_per_day()"
              :key="day.date"
              class="flex flex-col items-center min-w-0 flex-1 mx-1"
            >
              <div
                class="bg-blue-500 w-full rounded-t min-h-[4px] transition-all duration-300"
                :style="{
                  height: `${Math.max(4, (day.total_games / get_max_value(get_chart_data_for_games_per_day())) * 180)}px`
                }"
              ></div>
              <div class="mt-2 text-xs text-center font-medium">{{ day.total_games }}</div>
              <div class="text-xs text-gray-600 text-center">{{ new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }}</div>
            </div>
          </div>
        </div>
      </Container>

      <!-- User Engagement Distribution -->
      <Container class="p-4">
        <h3 class="text-lg font-bold mb-4">User Game Distribution</h3>
        <div class="h-64">
          <div v-if="get_chart_data_for_user_distribution().length === 0" class="h-full flex items-center justify-center bg-gray-100 rounded">
            <span class="text-gray-500">No data available</span>
          </div>
          <div v-else class="h-full flex items-end justify-around bg-gray-50 rounded p-4">
            <div
              v-for="(segment, index) in get_chart_data_for_user_distribution()"
              :key="segment.label"
              class="flex flex-col items-center min-w-0 flex-1 mx-2"
            >
              <div
                class="w-full rounded-t min-h-[4px] transition-all duration-300"
                :class="{
                  'bg-green-500': index === 0,
                  'bg-yellow-500': index === 1,
                  'bg-red-500': index === 2
                }"
                :style="{
                  height: `${Math.max(4, (segment.value / get_max_value(get_chart_data_for_user_distribution())) * 180)}px`
                }"
              ></div>
              <div class="mt-2 text-xs text-center font-medium">{{ segment.value }}</div>
              <div class="text-xs text-gray-600 text-center">{{ segment.label }}</div>
            </div>
          </div>
        </div>
      </Container>

      <!-- Game Types Breakdown -->
      <Container class="p-4">
        <h3 class="text-lg font-bold mb-4">Games by Type</h3>
        <div class="h-64">
          <div v-if="get_chart_data_for_game_types().length === 0" class="h-full flex items-center justify-center bg-gray-100 rounded">
            <span class="text-gray-500">No data available</span>
          </div>
          <div v-else class="h-full flex items-end justify-around bg-gray-50 rounded p-4">
            <div
              v-for="(type, index) in get_chart_data_for_game_types()"
              :key="type.label"
              class="flex flex-col items-center min-w-0 flex-1 mx-1"
            >
              <div
                class="w-full rounded-t min-h-[4px] transition-all duration-300"
                :class="{
                  'bg-purple-500': index === 0,
                  'bg-blue-500': index === 1,
                  'bg-green-500': index === 2,
                  'bg-orange-500': index === 3,
                  'bg-pink-500': index >= 4
                }"
                :style="{
                  height: `${Math.max(4, (type.value / get_max_value(get_chart_data_for_game_types())) * 180)}px`
                }"
              ></div>
              <div class="mt-2 text-xs text-center font-medium">{{ type.value }}</div>
              <div class="text-xs text-gray-600 text-center capitalize">{{ type.label }}</div>
            </div>
          </div>
        </div>
      </Container>

      <!-- Tutorial vs Non-Tutorial Games Stacked Bar Chart -->
      <Container class="p-4">
        <h3 class="text-lg font-bold mb-4">Tutorial vs Non-Tutorial Games</h3>
        <div class="h-64">
          <div v-if="get_chart_data_for_games_per_day().length === 0" class="h-full flex items-center justify-center bg-gray-100 rounded">
            <span class="text-gray-500">No data available</span>
          </div>
          <div v-else class="h-full flex items-end justify-around bg-gray-50 rounded p-4">
            <div
              v-for="day in get_chart_data_for_games_per_day()"
              :key="day.date"
              class="flex flex-col items-center min-w-0 flex-1 mx-1"
            >
              <!-- Stacked bars -->
              <div class="w-full flex flex-col justify-end" :style="{ height: '180px' }">
                <!-- Non-tutorial games (bottom) -->
                <div
                  class="bg-blue-500 w-full min-h-[2px] transition-all duration-300"
                  :style="{
                    height: `${Math.max(2, ((day.total_games - day.tutorial_games) / get_max_value(get_chart_data_for_games_per_day())) * 180)}px`
                  }"
                ></div>
                <!-- Tutorial games (top) -->
                <div
                  class="bg-orange-500 w-full min-h-[2px] transition-all duration-300"
                  :style="{
                    height: `${Math.max(2, (day.tutorial_games / get_max_value(get_chart_data_for_games_per_day())) * 180)}px`
                  }"
                ></div>
              </div>

              <!-- Labels -->
              <div class="mt-2 text-xs text-center font-medium">{{ day.total_games }}</div>
              <div class="text-xs text-gray-600 text-center">{{ new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }}</div>
            </div>
          </div>

          <!-- Legend -->
          <div class="flex justify-center mt-4 space-x-4">
            <div class="flex items-center">
              <div class="w-3 h-3 bg-blue-500 rounded mr-2"></div>
              <span class="text-xs text-gray-600">Without Tutorial</span>
            </div>
            <div class="flex items-center">
              <div class="w-3 h-3 bg-orange-500 rounded mr-2"></div>
              <span class="text-xs text-gray-600">With Tutorial</span>
            </div>
          </div>
        </div>
      </Container>

      <!-- User Registrations -->
      <Container class="p-4">
        <h3 class="text-lg font-bold mb-4">User Registrations (Last 30 Days)</h3>
        <div class="h-64">
          <div v-if="!registrations?.data || registrations.data.length === 0" class="h-full flex items-center justify-center bg-gray-100 rounded">
            <span class="text-gray-500">No data available</span>
          </div>
          <div v-else class="h-full flex items-end justify-start bg-gray-50 rounded p-4 overflow-x-auto">
            <div
              v-for="day in registrations.data.slice(-14)"
              :key="day.period"
              class="flex flex-col items-center min-w-[30px] mx-0.5"
            >
              <div
                class="bg-indigo-500 w-full rounded-t min-h-[4px] transition-all duration-300"
                :style="{
                  height: `${Math.max(4, (day.registrations / Math.max(...registrations.data.map((d: any) => d.registrations))) * 180)}px`
                }"
              ></div>
              <div class="mt-2 text-xs text-center font-medium">{{ day.registrations }}</div>
              <div class="text-xs text-gray-600 text-center transform -rotate-45 origin-center mt-1">
                {{ new Date(day.period).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }}
              </div>
            </div>
          </div>
        </div>
      </Container>
    </div>

    <!-- Loading and Error States for Charts -->
    <div v-if="loading" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Container class="p-4 h-80 flex items-center justify-center" v-for="i in 4" :key="i">
        <span class="text-gray-500">Loading charts...</span>
      </Container>
    </div>

    <div v-if="error && !loading" class="grid grid-cols-1 gap-4">
      <Container class="p-4 text-center text-red-500">
        Error loading charts: {{ error }}
      </Container>
    </div>
  </div>

  </div>
</template>

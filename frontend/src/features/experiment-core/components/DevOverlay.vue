<script setup lang="ts">
import { computed, inject, onUnmounted, ref, watch, type Ref } from "vue";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { GraphExecutor } from "@/features/experiment-core"; ///////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////
// inject + state
const emit = defineEmits(["stateChanged"]);
const executor = inject<Ref<GraphExecutor>>("experiment-executor")!;
const is_expanded = ref(true);

///////////////////////////////////////////////////////////////
// helper functions
const toggle_overlay = () => (is_expanded.value = !is_expanded.value);

async function reset_experiment() {
  if (!executor?.value) return;
  await executor.value.reset();
  await executor.value.start();
  emit("stateChanged");
}
function next_node() {
  if (!executor?.value) return;
  executor.value.step();
  emit("stateChanged");
}
function last_node() {
  if (!executor?.value) return;
  executor.value.step_back();
  emit("stateChanged");
}
function next_trial() {
  if (!executor?.value) return;
  executor.value.next_trial();
  emit("stateChanged");
}

const is_trial_node = computed(() => executor?.value?.current_node?.type === "trial");

///////////////////////////////////////////////////////////////
// event log functionality
// refresh event logs when overlay expands and periodically
const event_logs = ref<any[]>([]);
let interval_id: NodeJS.Timeout | null = null;

function start_event_log_refresh() {
  if (interval_id) return; // already running
  interval_id = setInterval(() => {
    try {
      event_logs.value = executor.value?.data_collection.dev_events.reverse() || [];
    } catch (error) {
      console.warn("error refreshing event logs:", error);
    }
  }, 100);
}

function stop_event_log_refresh() {
  if (interval_id) {
    clearInterval(interval_id);
    interval_id = null;
  }
}

// start/stop refresh based on overlay visibility
watch(is_expanded, (is_open) => {
  if (is_open) {
    start_event_log_refresh();
  } else {
    stop_event_log_refresh();
  }
});

// cleanup on unmount
onUnmounted(() => {
  stop_event_log_refresh();
});
function get_event_color_class(event_type: string): string {
  switch (event_type) {
    case "node_visit":
      return "border-blue-400";
    case "trial_start":
      return "border-green-400";
    case "interaction":
      return "border-orange-400";
    default:
      return "border-gray-400";
  }
}

///////////////////////////////////////////////////////////////
// Experiment Information
const experiment_info = computed(() => [
  { label: "Experiment ID", value: executor.value?.graph.graph_data.id },
  { label: "Current Node", value: executor.value?.current_node?.id },
  { label: "Trial Index", value: executor.value?.current_trial_index },
  { label: "Total Trials", value: executor.value?.total_trial_count },
  { label: "Points", value: executor.value?.data_collection.total_points || 0 },
]);

// previous trial metadata
const previous_trial_metadata = computed(() => {
  const trials = executor.value?.data_collection.trial_data || [];
  if (trials.length === 0) return null;

  // find the most recent completed trial (has end_time)
  const completed_trials = trials.filter((t) => t.end_time);
  if (completed_trials.length === 0) return null;

  // sort by end_time and get the most recent
  const last_trial = completed_trials.sort((a, b) => (b.end_time || 0) - (a.end_time || 0))[0];

  return last_trial?.metadata || null;
});
</script>

<template>
  <div class="fixed bottom-0 left-0 p-2 z-50">
    <button
      v-if="!is_expanded"
      @click="toggle_overlay"
      class="w-12 h-12 bg-black bg-opacity-80 text-white rounded-full flex items-center justify-center shadow-lg"
    >
      🔧
    </button>

    <div
      v-if="is_expanded"
      class="w-200 h-96 bg-white/10 bg-opacity-95 backdrop-blur-sm rounded-lg shadow-xl border border-gray-200 flex flex-col"
    >
      <!-- header -->
      <div class="dev-header flex items-center justify-between p-3 border-b border-gray-200">
        <Button
          variant="ghost"
          @click="toggle_overlay"
          title="Close dev tools"
          class="text-gray-500 hover:text-gray-700 text-2xl"
        >
          ×
        </Button>
        <h3 class="font-semibold text-gray-800 text-sm">Experiment Developer Tools</h3>
      </div>

      <!-- body -->
      <div class="flex flex-row p-3 gap-3 h-full">
        <!-- Graph Control -->
        <div class="flex flex-col space-y-1 w-30">
          <div class="text-center leading-3 mb-2">Graph Control</div>
          <Separator orientation="horizontal" />
          <Button variant="blue" class="w-full" @click="reset_experiment">Reset</Button>
          <Button variant="green" @click="next_node">Next node</Button>
          <Button variant="red" @click="last_node">Last node</Button>
          <Button variant="purple" @click="next_trial" :disabled="!is_trial_node">Next trial</Button>
        </div>
        <Separator orientation="vertical" class="h-full" />

        <!-- Experiment Event Log -->
        <div class="flex flex-col w-80 h-76">
          <div class="text-center leading-3 mb-2">Event Log</div>
          <Separator orientation="horizontal" class="mb-2" />
          <div class="grid grid-cols-[auto_auto_1fr] overflow-y-auto max-h-72 text-xs space-y-1">
            <div v-if="event_logs.length === 0" class="text-gray-500 text-center p-4">No events recorded yet</div>
            <div
              v-else
              v-for="event in event_logs"
              :key="event.id"
              class="p-1 bg-gray-100 text-xs/1.5 border-l-2 col-span-3 grid grid-cols-subgrid"
              :class="get_event_color_class(event.event_type)"
            >
              <span class="font-medium mr-3">{{ event.event_type }}</span>
              <span class="text-gray-600 mr-2">{{ event.data.node_id }}</span>
              <span v-if="event.event_type === 'trial_start'" class="text-gray-600"
                >Trial #{{ event.data.trial_index }}</span
              >
              <span v-if="event.event_type === 'interaction' && event.data.cell" class="text-gray-600"
                >Cell ({{ event.data.cell.row }}, {{ event.data.cell.col }})</span
              >
            </div>
          </div>
        </div>
        <Separator orientation="vertical" class="mb-2" />

        <div class="flex flex-col w-71 max-h-fit">
          <!-- Experiment Info -->
          <div class="flex flex-col">
            <div class="text-center leading-3 mb-2">Experiment Info</div>
            <Separator orientation="horizontal" class="mb-2" />
            <div class="grid grid-cols-[auto_1fr] gap-1 text-xs font-mono">
              <template v-for="item in experiment_info">
                <div class="font-mono font-bold justify-self-end">{{ item.label }}:</div>
                <div>{{ item.value }}</div>
              </template>
            </div>
          </div>

          <!-- Previous Trial Metadata -->
          <div class="flex flex-col mt-4">
            <div class="text-center leading-3 mb-2">Previous Trial Metadata</div>
            <Separator orientation="horizontal" class="mb-2" />
            <div class="w-71 h-32">
              <pre class="text-xs font-mono overflow-auto h-full p-2 bg-gray-100 border border-gray-200 rounded">{{
                previous_trial_metadata ? JSON.stringify(previous_trial_metadata, null, 2) : "No completed trials"
              }}</pre>
            </div>
          </div>
        </div>
      </div>

      <div class="flex flex-col w-71 max-h-fit">asf</div>
    </div>
  </div>
</template>

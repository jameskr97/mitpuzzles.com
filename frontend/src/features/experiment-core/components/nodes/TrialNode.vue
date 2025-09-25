<script setup lang="ts">
import { computed, inject, onMounted, ref, type Ref } from "vue";
import type { graph_node, trial_meta } from "@/features/experiment-core/graph/types";
import type { processed_stimuli } from "@/features/experiment-core/stimuli/types";
import { StimuliLoader } from "@/features/experiment-core/stimuli/StimuliLoader";
import Container from "@/components/ui/Container.vue";
import { ComponentRegistry } from "@/features/experiment-core/ComponentRegistry";
import type { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const props = defineProps<{ node: graph_node }>();
const emit = defineEmits(["complete", "trialStart"]);

// trial state
const stimuli = ref<processed_stimuli | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const executor = inject<Ref<GraphExecutor | null>>("experiment-executor");
const trial_config = computed(() => props.node.config.meta as trial_meta);

// trial index from executor
const current_trial_index = computed(() => executor?.value?.current_trial_index || 0);

// load custom trial component if specified in meta
const custom_trial_component = computed(() => {
  if (!trial_config.value.trial_component) return null;

  // get experiment id from executor
  const experiment_id = executor?.value?.graph.graph_data.id;
  if (!experiment_id) return null;

  return ComponentRegistry.get_component(experiment_id, trial_config.value.trial_component);
});

const current_stimulus_item = computed(() => {
  if (!stimuli.value || current_trial_index.value >= stimuli.value.items.length) {
    return null;
  }
  return stimuli.value.items[current_trial_index.value]; // could be single stimulus or array of n stimuli
});

async function load_stimuli() {
  try {
    loading.value = true;
    error.value = null;
    stimuli.value = await StimuliLoader.load_stimuli(trial_config.value.stimuli);

    // console.log(`loaded ${stimuli.value.total_count} trials from ${trial_config.value.stimuli.source}`);
    // console.log(`format: ${stimuli.value.format}`);

    // reset trial progress for this node
    if (executor?.value) {
      executor.value.reset_trial_progress(props.node.id);
    }

    // emit trial start for first trial
    if (stimuli.value.total_count > 0) {
      emit("trialStart");
    }
  } catch (err) {
    console.error("failed to load stimuli:", err);
    error.value = err instanceof Error ? err.message : "unknown error loading stimuli";
  } finally {
    loading.value = false;
  }
}

function handle_trial_complete(result: any) {
  if (!executor?.value) return;

  // record result and advance trial in executor
  executor.value.record_trial_result({
    stimuli: current_stimulus_item.value,
    result,
  });

  // advance to next trial or complete node
  const has_more_trials = executor.value.next_trial();

  if (!has_more_trials) {
    // node completed, executor.next_trial() already called step()
    return;
  } else {
    // emit trial start for next trial
    emit("trialStart");
  }
}

function handle_custom_trial_complete() {
  // handle completion from custom trial component
  handle_trial_complete({ completed: true, custom_component: true });
}

onMounted(async () => await load_stimuli());
</script>

<template>
  <div class="trial-node max-w-3xl mx-auto self-start">
    <!-- loading state -->
    <div v-if="loading" class="loading-state text-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
      <p class="text-gray-600">loading stimuli...</p>
    </div>

    <!-- error state -->
    <div v-else-if="error" class="error-state bg-red-50 border border-red-200 rounded-lg p-6 text-center">
      <h3 class="text-lg font-semibold text-red-800 mb-2 lowercase">error loading stimuli</h3>
      <p class="text-red-600 mb-4">{{ error }}</p>
      <button
        @click="load_stimuli"
        class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors lowercase"
      >
        retry
      </button>
    </div>

    <!-- trial content -->
    <div v-else-if="current_stimulus_item">
      <!-- custom trial component -->
      <div v-if="custom_trial_component" class="mb-2 w-full">
        <component
          :is="custom_trial_component"
          :stimulus_item="current_stimulus_item"
          :trial_index="executor?.current_trial_index"
          @trial-complete="handle_custom_trial_complete"
          :key="current_stimulus_item"
        />
      </div>

      <!-- fallback placeholder for when no custom trial component specified -->
      <Container v-else class="trial-placeholder rounded-lg p-2">
        <h3 class="flex flex-col font-semibold">Stimuli Count: {{ current_stimulus_item.length }}</h3>

        <div class="grid grid-cols-2 bg-red-100 border border-red-200 rounded">
          <div v-for="(stimulus, index) in current_stimulus_item" :key="index" class="m-2 p-2 bg-green-100 rounded">
            <div>Stimulus #{{ index }}</div>
            <Separator class="mb-1" />
            <div>{{ stimulus }}</div>
          </div>
        </div>

        <Button
          variant="blue"
          class="mt-2"
          @click="handle_trial_complete({ placeholder: true, score: Math.random() * 100 })"
        >
          Complete trial
        </Button>
      </Container>
    </div>

    <!-- completion state -->
    <div v-else class="completion-state text-center py-12">
      <div class="text-green-600 text-6xl mb-4">✓</div>
      <h3 class="text-xl font-semibold text-gray-800 lowercase">all trials completed!</h3>
      <p class="text-gray-600 mt-2">all trials completed</p>
    </div>
  </div>
</template>

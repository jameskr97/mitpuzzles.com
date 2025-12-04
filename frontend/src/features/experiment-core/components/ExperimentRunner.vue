<script setup lang="ts">
import { computed, onMounted, provide, ref } from "vue";
import { useRoute } from "vue-router";
import type { execution_state } from "@/features/experiment-core/graph/GraphExecutor";
import { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import Container from "@/core/components/ui/Container.vue";
import DevOverlay from "@/features/experiment-core/components/DevOverlay.vue";
import ProgressBar from "@/core/components/ProgressBar.vue";
import ExperimentPointsDisplay from "@/features/experiment-core/components/ExperimentPointsDisplay.vue";
import { node_type } from "@/features/experiment-core";
import { ExperimentLoader } from "@/features/experiment-core/ExperimentLoader.ts";
import ConsentNode from "@/features/experiment-core/components/nodes/ConsentNode.vue";
import TrialNode from "@/features/experiment-core/components/nodes/TrialNode.vue";
import DataUploadNode from "@/features/experiment-core/components/nodes/DataUploadNode.vue";
import RedirectToSourceNode from "@/features/experiment-core/components/nodes/RedirectToSourceNode.vue";
import InstructionsNode from "@/features/experiment-core/components/nodes/InstructionsNode.vue";
import SurveyNode from "@/features/experiment-core/components/nodes/SurveyNode.vue";
import { ComponentRegistry } from "@/features/experiment-core/ComponentRegistry.ts";

// composables
const route = useRoute();

// experiment state
const is_dev = import.meta.env.DEV;
const executor = ref<GraphExecutor | null>(null);
const execution_state_ref = ref<execution_state | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
provide("experiment-executor", executor);

// init experiment
onMounted(async () => {
  try {
    loading.value = true;
    error.value = null;
    const experiment_definition = await ExperimentLoader.load_experiment(route.params.experiment_id as string);
    executor.value = new GraphExecutor(experiment_definition);

    await executor.value.start();
    execution_state_ref.value = executor.value.state;
  } catch (err) {
    console.error("failed to initialize experiment:", err);
    error.value = err instanceof Error ? err.message : "unknown error";
  } finally {
    loading.value = false;
  }
});

// updating functions
function handle_node_complete() {
  if (!executor.value) return;

  executor.value.step();
  execution_state_ref.value = executor.value.state;
}

/**
 * refreshes execution state and trial progress
 * IMPORTANT: call this function whenever trials complete to update progress bar
 **/
function refresh_execution_state() {
  if (!executor.value) return;
  execution_state_ref.value = executor.value.state;
}

function is_experiment_complete(): boolean {
  if (!execution_state_ref.value) return false; // is the execution_state_ref doesn't exist, we're not we're not complete
  if (execution_state_ref.value.is_running) return false; // if execution graph is running, we're not complete.
  return true;
}

// node renderer
const has_custom_component = computed(() => !!executor.value!.current_node?.config?.component);
const loaded_custom_component = computed(() => {
  if (!executor.value?.current_node || !has_custom_component.value) return null;
  const component_name = executor.value.current_node.config.component;
  if (!component_name) return null;

  // look up component in registry
  const component = ComponentRegistry.get_component(
    executor?.value.graph.graph_data.id!, // force unwrap because it's been verified at this point
    component_name,
  );

  if (!component) {
    console.error(`component not found: ${component_name} for experiment: ${executor?.value.graph.graph_data.title}`);
    return null;
  }
  return component;
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <ProgressBar
      v-if="executor?.current_node?.type === node_type.TRIAL"
      :current_step="executor.global_progress.current + 1"
      :segments="executor.global_progress.total"
      :show_numerical_progress="true"
      class="order-first"
    />
    <ExperimentPointsDisplay
      v-if="executor?.current_node?.type === node_type.TRIAL && executor?.current_node?.config.meta.show_points"
    />

    <!-- main content -->
    <div class="flex-1 flex justify-center">
      <!-- loading state -->
      <div v-if="loading" class="text-center">
        <div class="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p class="text-gray-600">Loading experiment...</p>
      </div>

      <!-- error state -->
      <Container v-else-if="error" class="text-center max-w-md">
        <div class="text-red-600 text-4xl mb-4">⚠️</div>
        <h2 class="text-xl font-semibold text-red-800 mb-2">Experiment Error</h2>
        <p class="text-red-600 mb-4">{{ error }}</p>
      </Container>

      <!-- experiment complete -->
      <Container v-else-if="is_experiment_complete()" class="text-center max-w-md">
        <div class="text-green-600 text-6xl mb-6">✓</div>
        <h2 class="text-2xl font-semibold text-gray-800 mb-4">Experiment Complete</h2>
        <p class="text-gray-600">Thank you for participating in this study.</p>
      </Container>

      <!-- active experiment -->
      <div v-else-if="executor && execution_state_ref" class="w-full max-w-4xl">
        <!--        <NodeRenderer :node="executor.current_node" @complete="handle_node_complete" @trial-start="handle_trial_start" />-->
        <div class="flex items-center justify-center w-full">
          <div v-if="!executor.current_node" class="text-center italic text-gray-500">
            <p>no node to display</p>
          </div>

          <div v-else class="flex justify-center w-full">
            <!-- custom component takes priority -->
            <component
              v-if="loaded_custom_component"
              :is="loaded_custom_component"
              :node="executor.current_node"
              @complete="handle_node_complete"
            />

            <!-- fallback to default components -->
            <ConsentNode v-else-if="executor.current_node.type === node_type.CONSENT" :node="executor.current_node" @complete="handle_node_complete" />
            <InstructionsNode v-else-if="executor.current_node.type === node_type.INSTRUCTIONS" :node="executor.current_node" @complete="handle_node_complete" />
            <SurveyNode v-else-if="executor.current_node.type === node_type.SURVEY" :node="executor.current_node" @complete="handle_node_complete" />
            <DataUploadNode v-else-if="executor.current_node.type === node_type.DATA_UPLOAD" :node="executor.current_node" @complete="handle_node_complete" />
            <RedirectToSourceNode v-else-if="executor.current_node.type === node_type.PROLIFIC_REDIRECT" :node="executor.current_node" @complete="handle_node_complete" />

            <TrialNode
              v-else-if="executor.current_node.type === node_type.TRIAL"
              :node="executor.current_node"
              :key="executor.current_node.id"
              @complete="handle_node_complete"
              @trial-start="$emit('trialStart')"
            />

            <!-- error loading custom component -->
            <div v-else-if="has_custom_component && !loaded_custom_component" class="loading-error">
              <h3>component loading error</h3>
              <p>
                component "{{ executor.current_node.config.component }}" not found for experiment "{{
                  executor?.graph.graph_data.id
                }}"
              </p>
              <button @click="handle_node_complete" class="continue-button">Continue Anyway</button>
            </div>

            <!-- placeholder for unimplemented node types -->
            <div v-else class="unimplemented-node">
              <div class="placeholder-content">
                <h3>{{ `${executor.current_node.type} node` }}</h3>
                <p>node type "{{ executor.current_node.type }}" not yet implemented</p>
                <div class="node-info">
                  <strong>node id:</strong> {{ executor.current_node.id }}<br />
                  <strong>config:</strong> {{ JSON.stringify(executor.current_node.config, null, 2) }}
                </div>
                <button @click="handle_node_complete" class="continue-button">continue (placeholder)</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- dev overlay (only in development) -->
    <DevOverlay v-if="is_dev" @state-changed="refresh_execution_state" />
  </div>
</template>

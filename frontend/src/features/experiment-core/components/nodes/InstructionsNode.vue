<script setup lang="ts">
import type { graph_node } from "@/features/experiment-core//graph/types";
import InstructionHeader from "@/features/experiment-core/components/InstructionHeader.vue";
import { inject, type Ref } from "vue";
import type { GraphExecutor } from "@/features/experiment-core";

const props = defineProps<{ node: graph_node }>();
const executor = inject<Ref<GraphExecutor>>("experiment-executor");

defineEmits(["complete"]);
</script>

<template>
  <div class="max-w-[600px] mx-auto p-5 bg-white rounded-lg shadow-md font-sans md:mx-2.5 md:p-4">
    <div v-if="props.node.config.content" v-html="props.node.config.content"></div>
    <div v-else class="text-gray-600">
      <InstructionHeader>Instructions</InstructionHeader>
      <div>
        These are the default instructions. Define an `instructions.vue` in your <code class="italic font-bold">experiment-defintions/{{ executor?.graph.graph_data.id }}</code> folder to
        have this be updated with that.
      </div>
    </div>
  </div>
</template>

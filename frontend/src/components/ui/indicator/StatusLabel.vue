<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import { cn } from "@/lib/utils";

const props = defineProps<{
  class?: HTMLAttributes["class"];
}>();
</script>

<template>
  <span :class="cn(props.class)" v-bind="$attrs">
    <slot>
      <span class="hidden group-[.online]:block">Online</span>
      <span class="hidden group-[.offline]:block">Offline</span>
      <span class="hidden group-[.maintenance]:block">Maintenance</span>
      <span class="hidden group-[.degraded]:block">Degraded</span>
    </slot>
  </span>
</template>

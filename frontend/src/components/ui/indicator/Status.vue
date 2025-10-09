<script setup lang="ts">
import type { PrimitiveProps } from "reka-ui";
import type { HTMLAttributes } from "vue";
import { reactiveOmit } from "@vueuse/core";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusType = 'online' | 'offline' | 'maintenance' | 'degraded';

const props = defineProps<
  PrimitiveProps & {
    status: StatusType;
    class?: HTMLAttributes["class"];
  }
>();

const delegatedProps = reactiveOmit(props, "class", "status");
</script>

<template>
  <Badge
    :class="cn('flex items-center gap-2', 'group', props.status, props.class)"
    variant="ghost"
    v-bind="delegatedProps"
  >
    <slot />
  </Badge>
</template>

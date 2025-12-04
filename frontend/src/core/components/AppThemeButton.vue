<script setup lang="ts">
import { useColorMode } from "@vueuse/core";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/core/components/ui/dropdown-menu";
import type { PropType } from "vue";

const colorMode = useColorMode({ disableTransition: false });
colorMode.value = "light";
type Align = "start" | "center" | "end" | undefined;

const props = defineProps({
  mode: {
    type: Object as PropType<Align>,
  },
});
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <slot></slot>
    </DropdownMenuTrigger>
    <DropdownMenuContent :align="props.mode ?? 'end'">
      <DropdownMenuItem @click="colorMode = 'light'">{{ $t('ui:theme.light') }}</DropdownMenuItem>
      <DropdownMenuItem @click="colorMode = 'dark'">{{ $t('ui:theme.dark') }}</DropdownMenuItem>
      <DropdownMenuItem @click="colorMode = 'auto'">{{ $t('ui:theme.system') }}</DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

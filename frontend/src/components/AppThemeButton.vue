<script setup lang="ts">
import { useColorMode } from "@vueuse/core";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { PropType } from "vue";

const colorMode = useColorMode({ disableTransition: false });
colorMode.value = "light"
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
      <DropdownMenuItem @click="colorMode = 'light'"> Light </DropdownMenuItem>
      <DropdownMenuItem @click="colorMode = 'dark'"> Dark </DropdownMenuItem>
      <DropdownMenuItem @click="colorMode = 'auto'"> System </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

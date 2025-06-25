<script setup lang="ts">
import { useColorMode } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { withDefault } from "reka-ui";

const colorMode = useColorMode({ disableTransition: false })
type Align = "start" | "center" | "end" | undefined;

const props = defineProps({
  mode: {
    type: Object as PropType<Align>,
  }
})
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="outline">
        <v-icon name="bi-moon-stars-fill" class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
        <v-icon name="bi-sun-fill" class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        <span class="sr-only">Toggle theme</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent :align="props.mode ?? 'end'">
      <DropdownMenuItem @click="colorMode = 'light'">
        Light
      </DropdownMenuItem>
      <DropdownMenuItem @click="colorMode = 'dark'">
        Dark
      </DropdownMenuItem>
      <DropdownMenuItem @click="colorMode = 'auto'">
        System
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

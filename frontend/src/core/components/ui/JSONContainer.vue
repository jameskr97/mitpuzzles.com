<script setup lang="ts">
import { computed } from 'vue'
import Container from '@/core/components/ui/Container.vue'

const props = defineProps<{
  data: any
  title?: string
}>()

function format_json(obj: any): string {
  const json_string = JSON.stringify(
    obj,
    (key, value) => {
      // Compact 1D arrays onto single line
      if (Array.isArray(value) && value.length > 0 && !Array.isArray(value[0])) {
        return `[${value.join(", ")}]`
      }
      return value
    },
    2,
  ).replace(/"\[([^\]]+)\]"/g, "[$1]")

  // Add syntax highlighting spans
  return json_string
    .replace(/"([\w_]+)":/g, '<span class="json-key">"$1"</span>:')
    .replace(/:\s*(".*?")/g, ': <span class="json-string">$1</span>')
    .replace(/:\s*(-?\d+(?:\.\d+)?)/g, ': <span class="json-number">$1</span>')
    .replace(/:\s*(true|false)/g, ': <span class="json-boolean">$1</span>')
    .replace(/(\[|\]|\{|\})/g, '<span class="json-bracket">$1</span>')
}

const formatted_html = computed(() => format_json(props.data))
</script>

<template>
  <Container class="overflow-scroll flex flex-col json-viewer">
    <pre class="text-xs leading-relaxed"><code v-html="formatted_html" /></pre>
  </Container>
</template>

<style scoped>
.json-viewer,
.json-viewer * {
  font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace !important;
  background: #1f1f28; /* sumiInk3 */
  color: #dcd7ba; /* fujiWhite */
}

/* Syntax Highlighting Colors */
.json-viewer :deep(.json-key) { color: #7e9cd8; } /* crystalBlue */
.json-viewer :deep(.json-string) { color: #98bb6c; } /* springGreen */
.json-viewer :deep(.json-number) { color: #d27e99; } /* sakuraPink */
.json-viewer :deep(.json-boolean) { color: #e46876; } /* waveRed */
.json-viewer :deep(.json-bracket) { color: #e6c384; } /* carpYellow */
</style>

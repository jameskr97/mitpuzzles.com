<script setup lang="ts">
/**
 * This component is used to render markdown files.
 * Not intended to be used directly, but rather through the "route.markdown"
 * function inside main.ts.
 */
import MarkdownIt from "markdown-it";
const props = defineProps<{
  content: string;
  proseClass?: string;
}>();

const md = MarkdownIt({ html: true, linkify: true, typographer: true });
md.linkify.set({ fuzzyLink: false });
const html = md.render(props.content);
</script>

<template>
  <div class="mx-auto prose" :class="proseClass" v-html="html"></div>
</template>

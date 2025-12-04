<script setup lang="ts">
/**
 * This component is used to render markdown files.
 * Not intended to be used directly, but rather through the "route.markdown"
 * function inside main.ts.
 */
import MarkdownIt from "markdown-it";
import Container from "@/core/components/ui/Container.vue";
const props = defineProps<{
  content: string;
  proseClass?: string;
}>();

const md = MarkdownIt({ html: true, linkify: true, typographer: true });
md.linkify.set({ fuzzyLink: false });
const html = md.render(props.content);
</script>

<template>
  <Container class="prose prose-sm prose-tight mx-auto
      [&_h1]:mb-1 [&_h1]:mt-2
      [&_h2]:mt-4 [&_h2]:mb-1
      [&_h3]:mt-2 [&_h3]:mb-1
      [&_p]:my-1
      [&_ul]:my-1 [&_ul]:space-y-0
      [&_li]:my-0" :class="proseClass" v-html="html"></Container>
</template>

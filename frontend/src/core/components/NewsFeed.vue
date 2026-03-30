<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import MarkdownIt from "markdown-it";
import Container from "@/core/components/ui/Container.vue";
import type { NewsPost } from "@/core/types";

const md = MarkdownIt({ html: false, linkify: true, typographer: true });

const posts = ref<NewsPost[]>([]);
const loading = ref(true);
const has_more = ref(false);
const total = ref(0);

function format_date(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function render_markdown(content: string): string {
  return md.render(content);
}

async function load_feed() {
  try {
    const res = await fetch("/api/news/feed?limit=5", { credentials: "include" });
    if (!res.ok) return;
    const data = await res.json();
    posts.value = data.posts;
    has_more.value = data.has_more;
    total.value = data.total;
  } finally {
    loading.value = false;
  }
}

onMounted(load_feed);
</script>

<template>
  <Container v-if="!loading" class="h-100 flex flex-col">
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3 shrink-0">News & Updates</div>
    <div class="flex flex-col divide-y divide-gray-200 overflow-y-auto min-h-0">
      <div v-for="post in posts" :key="post.id" class="py-3 first:pt-0 last:pb-0">
        <div class="text-xs text-gray-400 mb-1">{{ format_date(post.published_at) }}<span v-if="post.author_username"> &mdash; {{ post.author_username }}</span></div>
        <div
          class="prose prose-sm prose-tight
            [&_h1]:mb-1 [&_h1]:mt-1
            [&_h2]:mt-2 [&_h2]:mb-1
            [&_h3]:mt-1 [&_h3]:mb-1
            [&_p]:my-1
            [&_ul]:my-1 [&_ul]:space-y-0
            [&_li]:my-0"
          v-html="render_markdown(post.content)"
        />
      </div>
    </div>
    <router-link v-if="has_more" to="/news" class="text-xs text-blue-600 hover:underline mt-2 block text-center">
      view all updates
    </router-link>
  </Container>
</template>

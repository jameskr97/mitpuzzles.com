<script setup lang="ts">
import { ref, computed } from "vue";
import { useAsyncState } from "@vueuse/core";
import MarkdownIt from "markdown-it";
import Container from "@/core/components/ui/Container.vue";
import { Button } from "@/core/components/ui/button";
import { Textarea } from "@/core/components/ui/textarea";
import { Switch } from "@/core/components/ui/switch";
import { Label } from "@/core/components/ui/label";
import { Badge } from "@/core/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/core/components/ui/dialog";

const md = MarkdownIt({ html: false, linkify: true, typographer: true });

interface NewsPost {
  id: string;
  created_at: string;
  updated_at: string;
  content: string;
  is_published: boolean;
  published_at: string | null;
}

const { state: posts, isLoading: loading, execute: fetch_posts } = useAsyncState(
  async () => {
    const res = await fetch("/api/news/admin/list", { credentials: "include" });
    if (!res.ok) return [];
    return (await res.json()) as NewsPost[];
  },
  [] as NewsPost[],
  { resetOnExecute: false },
);

// editor state
const editor_open = ref(false);
const editing_id = ref<string | null>(null);
const editor_content = ref("");
const editor_published = ref(false);
const saving = ref(false);

const preview_html = computed(() => md.render(editor_content.value));

function format_date(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit",
  });
}


function open_new() {
  editing_id.value = null;
  editor_content.value = "";
  editor_published.value = false;
  editor_open.value = true;
}

function open_edit(post: NewsPost) {
  editing_id.value = post.id;
  editor_content.value = post.content;
  editor_published.value = post.is_published;
  editor_open.value = true;
}

async function save() {
  saving.value = true;
  try {
    if (editing_id.value) {
      await fetch(`/api/news/admin/${editing_id.value}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ content: editor_content.value, is_published: editor_published.value }),
      });
    } else {
      await fetch("/api/news/admin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ content: editor_content.value, is_published: editor_published.value }),
      });
    }
    editor_open.value = false;
    await fetch_posts();
  } finally {
    saving.value = false;
  }
}

async function delete_post(id: string) {
  if (!confirm("Delete this post?")) return;
  await fetch(`/api/news/admin/${id}`, { method: "DELETE", credentials: "include" });
  await fetch_posts();
}

</script>

<template>
  <div class="flex flex-col gap-2 w-full items-center">
    <Container class="max-w-4xl w-full">
      <div class="flex items-center justify-between mb-4">
        <div class="text-2xl font-semibold">News Manager</div>
        <Button @click="open_new">New Post</Button>
      </div>
    </Container>

    <Container class="max-w-4xl w-full">
      <div v-if="loading" class="text-muted-foreground text-center py-8">Loading...</div>
      <div v-else-if="posts.length === 0" class="text-muted-foreground text-center py-8">No posts yet.</div>
      <div v-else class="flex flex-col divide-y">
        <div v-for="post in posts" :key="post.id" class="py-3 first:pt-0 last:pb-0">
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <Badge :variant="post.is_published ? 'default' : 'secondary'">
                  {{ post.is_published ? "Published" : "Draft" }}
                </Badge>
                <span class="text-xs text-muted-foreground">{{ format_date(post.created_at) }}</span>
              </div>
              <div
                class="prose prose-sm prose-tight
                  [&_p]:my-0 [&_ul]:my-0 [&_li]:my-0"
                v-html="md.render(post.content)"
              />
            </div>
            <div class="flex gap-1 shrink-0">
              <Button variant="outline" size="sm" @click="open_edit(post)">Edit</Button>
              <Button variant="outline" size="sm" class="text-red-600" @click="delete_post(post.id)">Delete</Button>
            </div>
          </div>
        </div>
      </div>
    </Container>

    <!-- Editor dialog -->
    <Dialog v-model:open="editor_open">
      <DialogContent class="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ editing_id ? "Edit Post" : "New Post" }}</DialogTitle>
          <DialogDescription class="sr-only">Write a news update in markdown</DialogDescription>
        </DialogHeader>

        <div class="grid grid-cols-2 gap-4 mt-2">
          <!-- Editor -->
          <div class="flex flex-col gap-2">
            <Label class="text-xs text-muted-foreground uppercase">Markdown</Label>
            <Textarea
              v-model="editor_content"
              class="min-h-[300px] font-mono text-sm"
              placeholder="Write your update here..."
            />
          </div>

          <!-- Preview -->
          <div class="flex flex-col gap-2">
            <Label class="text-xs text-muted-foreground uppercase">Preview</Label>
            <div
              class="border rounded-md p-3 min-h-[300px] prose prose-sm prose-tight
                [&_h1]:mb-1 [&_h1]:mt-1
                [&_h2]:mt-2 [&_h2]:mb-1
                [&_h3]:mt-1 [&_h3]:mb-1
                [&_p]:my-1
                [&_ul]:my-1 [&_ul]:space-y-0
                [&_li]:my-0"
              v-html="preview_html"
            />
          </div>
        </div>

        <div class="flex items-center justify-between mt-4">
          <div class="flex items-center gap-2">
            <Switch v-model="editor_published" />
            <Label>Publish</Label>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" @click="editor_open = false">Cancel</Button>
            <Button :disabled="saving || !editor_content.trim()" @click="save">
              {{ saving ? "Saving..." : "Save" }}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

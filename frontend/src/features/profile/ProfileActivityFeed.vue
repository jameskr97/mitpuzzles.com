<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";

const props = defineProps<{
  activity: {
    date: string;
    entries: { icon: string; text: string; detail?: string }[];
  }[];
}>();

function format_activity_date(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }).toUpperCase();
}
</script>

<template>
  <Container>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Activity</div>
    <div v-if="activity.length === 0" class="text-sm text-gray-400 text-center py-4">no recent activity</div>
    <div v-else class="flex flex-col gap-3">
      <div v-for="day in activity" :key="day.date">
        <div class="text-xs font-semibold text-amber-700 mb-1">{{ format_activity_date(day.date) }}</div>
        <div class="flex flex-col gap-1.5">
          <div v-for="(entry, i) in day.entries" :key="i" class="flex items-start gap-2 text-sm">
            <span class="shrink-0 mt-0.5">{{ entry.icon }}</span>
            <div>
              <span>{{ entry.text }}</span>
              <span v-if="entry.detail" class="text-gray-400 ml-1">{{ entry.detail }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Container>
</template>

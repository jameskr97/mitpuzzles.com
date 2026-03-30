<script setup lang="ts">
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/core/components/ui/table";
import type { LeaderboardEntry } from "@/core/types";

withDefaults(defineProps<{
  entries: LeaderboardEntry[];
  time_label?: string;
}>(), {
  time_label: "Time",
});
</script>

<template>
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead class="p-0">{{ $t("ui:table.rank") }}</TableHead>
        <TableHead>{{ time_label }}</TableHead>
        <TableHead>{{ $t("ui:table.username") }}</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow
        v-for="(entry, index) in entries"
        :class="{ 'font-bold': entry.is_current_user }"
        :key="index"
      >
        <TableCell>{{ entry.rank }}</TableCell>
        <TableCell>{{ entry.duration_display }}</TableCell>
        <TableCell>
          <router-link :to="{ name: 'user-profile', params: { username: entry.username } }" class="hover:underline">
            {{ entry.username }}
          </router-link>
        </TableCell>
      </TableRow>
    </TableBody>
  </Table>
</template>

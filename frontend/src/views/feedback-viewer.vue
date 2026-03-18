<script setup lang="ts">
import type { ColumnDef, SortingState } from "@tanstack/vue-table";
import {
  FlexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useVueTable,
} from "@tanstack/vue-table";
import { ArrowUpDown } from "lucide-vue-next";
import { h, onMounted, ref } from "vue";
import { api } from "@/core/services/client";

import { valueUpdater } from "@/core/components/ui/table/utils";
import Container from "@/core/components/ui/Container.vue";
import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/core/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/core/components/ui/dialog";

interface FeedbackItem {
  id: string;
  created_at: string;
  message: string;
  feedback_metadata: Record<string, any> | null;
  user_id: string | null;
  user_email: string | null;
  is_authenticated: boolean;
}

const feedback_list = ref<FeedbackItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const selected_feedback = ref<FeedbackItem | null>(null);
const dialog_open = ref(false);

const format_date = (date_string: string) => {
  return new Date(date_string).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const format_date_full = (date_string: string) => {
  return new Date(date_string).toLocaleString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

const open_detail = (item: FeedbackItem) => {
  selected_feedback.value = item;
  dialog_open.value = true;
};

const columns: ColumnDef<FeedbackItem>[] = [
  {
    accessorKey: "created_at",
    header: ({ column }) => {
      return h(
        Button,
        {
          variant: "ghost",
          onClick: () => column.toggleSorting(column.getIsSorted() === "asc"),
        },
        () => ["Date", h(ArrowUpDown, { class: "ml-2 h-4 w-4" })]
      );
    },
    cell: ({ row }) => h("div", { class: "whitespace-nowrap" }, format_date(row.getValue("created_at"))),
  },
  {
    accessorKey: "user_email",
    header: "User",
    cell: ({ row }) => {
      const email = row.getValue("user_email") as string | null;
      if (email) {
        return h("div", {}, email);
      }
      return h("span", { class: "text-muted-foreground italic" }, "Anonymous");
    },
  },
  {
    accessorKey: "message",
    header: "Message",
    cell: ({ row }) =>
      h(
        "div",
        { class: "line-clamp-4 whitespace-pre-wrap max-w-md" },
        row.getValue("message")
      ),
  },
];

const sorting = ref<SortingState>([{ id: "created_at", desc: true }]);

const table = useVueTable({
  get data() {
    return feedback_list.value;
  },
  columns,
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getSortedRowModel: getSortedRowModel(),
  onSortingChange: (updaterOrValue) => valueUpdater(updaterOrValue, sorting),
  state: {
    get sorting() {
      return sorting.value;
    },
  },
});

const fetch_feedback = async () => {
  try {
    loading.value = true;
    error.value = null;
    const { data } = await api.GET("/api/feedback/admin/list");
    if (data) feedback_list.value = data;
  } catch (err) {
    error.value = "Failed to load feedback";
    console.error("Error fetching feedback:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetch_feedback();
});
</script>

<template>
  <div class="flex flex-col gap-2 w-full items-center">
    <Container class="max-w-4xl w-full">
      <div class="text-2xl font-semibold mb-4 text-center">Feedback</div>
    </Container>
    <Container class="max-w-4xl w-full">
      <div class="w-full">
        <div v-if="loading" class="text-muted-foreground text-center py-8">Loading...</div>
        <div v-else-if="error" class="text-red-500 text-center py-8">{{ error }}</div>
        <template v-else>
          <div class="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
                  <TableHead v-for="header in headerGroup.headers" :key="header.id">
                    <FlexRender
                      v-if="!header.isPlaceholder"
                      :render="header.column.columnDef.header"
                      :props="header.getContext()"
                    />
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <template v-if="table.getRowModel().rows?.length">
                  <TableRow
                    v-for="row in table.getRowModel().rows"
                    :key="row.id"
                    class="cursor-pointer"
                    @click="open_detail(row.original)"
                  >
                    <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                      <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
                    </TableCell>
                  </TableRow>
                </template>
                <TableRow v-else>
                  <TableCell :colspan="columns.length" class="h-24 text-center">
                    No feedback yet.
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
          <div class="flex items-center justify-end space-x-2 py-4">
            <div class="flex-1 text-sm text-muted-foreground">
              {{ table.getRowModel().rows.length }} feedback item(s)
            </div>
            <div class="space-x-2">
              <Button
                variant="outline"
                size="sm"
                :disabled="!table.getCanPreviousPage()"
                @click="table.previousPage()"
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                :disabled="!table.getCanNextPage()"
                @click="table.nextPage()"
              >
                Next
              </Button>
            </div>
          </div>
        </template>
      </div>
    </Container>

    <Dialog v-model:open="dialog_open">
      <DialogContent class="max-w-lg">
        <DialogHeader>
          <DialogTitle>Feedback Details</DialogTitle>
          <DialogDescription class="sr-only">
            Full details of the selected feedback entry
          </DialogDescription>
        </DialogHeader>

        <div v-if="selected_feedback" class="space-y-4">
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <span class="text-muted-foreground">From:</span>
              <span v-if="selected_feedback.user_email">{{ selected_feedback.user_email }}</span>
              <span v-else class="italic text-muted-foreground">Anonymous</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-muted-foreground">Date:</span>
              <span>{{ format_date_full(selected_feedback.created_at) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-muted-foreground">Status:</span>
              <Badge :variant="selected_feedback.is_authenticated ? 'blue' : 'secondary'">
                {{ selected_feedback.is_authenticated ? "Authenticated" : "Anonymous" }}
              </Badge>
            </div>
          </div>

            <div class="text-muted-foreground mb-1">Message:</div>
            <div class="bg-muted/50 p-3 rounded-md overflow-y-scroll w-120">
              {{ selected_feedback.message }}

            </div>

          <div v-if="selected_feedback.feedback_metadata">
            <div class="text-muted-foreground mb-1">Metadata:</div>
            <pre class="bg-muted/50 p-3 rounded-md text-sm overflow-x-auto">{{
              JSON.stringify(selected_feedback.feedback_metadata, null, 2)
            }}</pre>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import { useVisitorStore } from "@/store/visitor.ts";
import { ref } from "vue";
import { Label } from "reka-ui";
import { Input } from "@/components/ui/input";

const visitor = useVisitorStore();
const dialog_visible = ref(false);
const username_entry = ref("");
const error = ref("");
const change_username = async () => {
  const res = await visitor.changeUsername(username_entry.value);
  if (res && res.changed) {
    username_entry.value = "";
    dialog_visible.value = false;
  } else {
    if (res && "error" in res) error.value = res.error.toString();
  }
};
</script>

<template>
  <Dialog v-model:open="dialog_visible">
    <DialogTrigger as-child>
      <slot name="trigger"></slot>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Change Username</DialogTitle>
        <DialogDescription>Click save when you're done.</DialogDescription>
      </DialogHeader>
      <div class="flex flex-col gap-2">
        <form class="flex flex-row items-center gap-4" @submit.prevent="change_username">
          <Label for="username" class="text-right">Username</Label>
          <Input v-model="username_entry" id="username" :placeholder="visitor.generated_username" class="col-span-3" />
        </form>
        <span v-if="error" class="text-red-500">{{ error }}</span>
      </div>

      <DialogFooter>
        <Button type="submit" @click="change_username">Save</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

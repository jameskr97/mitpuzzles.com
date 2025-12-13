<script setup lang="ts">
import { ref } from "vue";

const props = withDefaults(
  defineProps<{
    accept?: string[];
  }>(),
  {
    accept: () => [],
  }
);

const emit = defineEmits<{
  "files-added": [files: File[]];
}>();

const is_dragging = ref(false);
const file_input_ref = ref<HTMLInputElement | null>(null);

const filter_files = (files: FileList | File[]): File[] => {
  if (props.accept.length === 0) {
    return Array.from(files);
  }
  return Array.from(files).filter((f) => props.accept.some((ext) => f.name.endsWith(ext)));
};

const handle_drop = (event: DragEvent) => {
  event.preventDefault();
  is_dragging.value = false;

  if (event.dataTransfer?.files) {
    const filtered = filter_files(event.dataTransfer.files);
    if (filtered.length > 0) {
      emit("files-added", filtered);
    }
  }
};

const handle_drag_over = (event: DragEvent) => {
  event.preventDefault();
  is_dragging.value = true;
};

const handle_drag_leave = (event: DragEvent) => {
  event.preventDefault();
  is_dragging.value = false;
};

const handle_file_input = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    const filtered = filter_files(target.files);
    if (filtered.length > 0) {
      emit("files-added", filtered);
    }
    target.value = "";
  }
};

const open_file_picker = () => {
  file_input_ref.value?.click();
};

defineExpose({
  open_file_picker,
});
</script>

<template>
  <div
    class="relative min-h-[300px] rounded-lg border-4 border-dashed transition-colors"
    :class="is_dragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'"
    @drop="handle_drop"
    @dragover="handle_drag_over"
    @dragleave="handle_drag_leave"
  >
    <input
      ref="file_input_ref"
      type="file"
      :accept="accept.join(',')"
      multiple
      class="hidden"
      @change="handle_file_input"
    />

    <slot :is_dragging="is_dragging" :open_file_picker="open_file_picker" />

    <div v-if="$slots.footer" @click="open_file_picker">
      <slot name="footer" :is_dragging="is_dragging" />
    </div>
  </div>
</template>

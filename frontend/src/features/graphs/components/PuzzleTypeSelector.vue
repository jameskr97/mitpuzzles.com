<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { ACTIVE_GAMES } from "@/constants";
import { api } from "@/core/services/client";

const props = withDefaults(
  defineProps<{
    puzzleType?: string;
    puzzleSize?: string;
    puzzleDifficulty?: string;
  }>(),
  {
    puzzleType: "",
    puzzleSize: "",
    puzzleDifficulty: "",
  },
);

const emit = defineEmits<{
  (e: "update", value: { puzzle_type: string; puzzle_size: string; puzzle_difficulty: string }): void;
}>();

const selected_type = ref(props.puzzleType || Object.keys(ACTIVE_GAMES)[0]);
const selected_size = ref(props.puzzleSize);
const selected_difficulty = ref(props.puzzleDifficulty);

// available variants from the API
const variants = ref<{ size: string; difficulty: string | null }[]>([]);
const sizes = ref<string[]>([]);
const difficulties = ref<string[]>([]);

async function load_variants() {
  const { data } = await api.GET("/api/puzzle/definition/types");
  if (!data) return;

  const config = (data as any)[selected_type.value];
  if (!config) {
    variants.value = [];
    sizes.value = [];
    difficulties.value = [];
    return;
  }

  variants.value = config.available_difficulties ?? [];
  sizes.value = [...new Set(variants.value.map((v) => v.size))];
  difficulties.value = [...new Set(variants.value.map((v) => v.difficulty).filter(Boolean))] as string[];

  // reset if current selection isn't valid
  if (selected_size.value && !sizes.value.includes(selected_size.value)) {
    selected_size.value = "";
  }
  if (selected_difficulty.value && !difficulties.value.includes(selected_difficulty.value)) {
    selected_difficulty.value = "";
  }
}

function emit_update() {
  emit("update", {
    puzzle_type: selected_type.value,
    puzzle_size: selected_size.value,
    puzzle_difficulty: selected_difficulty.value,
  });
}

watch(selected_type, async () => {
  selected_size.value = "";
  selected_difficulty.value = "";
  await load_variants();
  emit_update();
});

watch([selected_size, selected_difficulty], emit_update);

onMounted(async () => {
  await load_variants();
  emit_update();
});
</script>

<template>
  <div class="flex gap-2 items-center">
    <select v-model="selected_type" class="text-xs border rounded px-1.5 py-1">
      <option v-for="t in Object.keys(ACTIVE_GAMES)" :key="t" :value="t">{{ t }}</option>
    </select>
    <select v-model="selected_size" class="text-xs border rounded px-1.5 py-1">
      <option value="">all sizes</option>
      <option v-for="s in sizes" :key="s" :value="s">{{ s }}</option>
    </select>
    <select v-model="selected_difficulty" class="text-xs border rounded px-1.5 py-1">
      <option value="">all difficulties</option>
      <option v-for="d in difficulties" :key="d" :value="d">{{ d }}</option>
    </select>
  </div>
</template>

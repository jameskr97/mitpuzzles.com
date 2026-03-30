<script setup lang="ts">
/** PlaybackTimeline — canvas-based timeline with:
 * - event marker + draggable scrubber
 * -
 * status bar, tick marks, and draggable scrubber.
 */
import { ref, watch, onMounted, onUnmounted, computed } from "vue";
import type { PlaybackFrame } from "@/core/types";

// constants for sizing + playback
const MPS_OPTIONS = [2, 5, 10];
const SIZES = {
  default: { slot: 28, height: 48, statusBar: 4, iconY: 23, tickY: 40, tickH: 6, iconSize: 26, font: "18px" },
  small: { slot: 20, height: 30, statusBar: 3, iconY: 14, tickY: 25, tickH: 4, iconSize: 16, font: "12px" },
};

const props = withDefaults(defineProps<{
    frames: PlaybackFrame[];
    current_frame: number;
    is_playing: boolean;
    moves_per_second: number;
    size?: "default" | "small";
  }>(),
  {
    size: "default",
  },
);

const emit = defineEmits<{
  (e: "seek", frame: number): void;
  (e: "toggle-play"): void;
  (e: "set-mps", mps: number): void;
}>();

// canvas reference + state
const canvas_ref = ref<HTMLCanvasElement | null>(null);
const container_ref = ref<HTMLDivElement | null>(null);
const is_dragging = ref(false);

// preload icon images
const mouse_left_img = new Image();
mouse_left_img.src = "/assets/icons/mouse_left_outline.svg";
mouse_left_img.onload = () => draw();

const S = computed(() => SIZES[props.size]);
const canvas_width = computed(() => props.frames.length * S.value.slot + S.value.slot);

// colors
function get_status_color(action: string): string {
  if (action === "initial") return "transparent";
  if (action === "clear") return "#f97316";
  if (action === "attempt_solve" || action === "attempt_solve_success") return "#3b82f6";
  if (action === "attempt_solve_fail") return "#ef4444";
  return "#22c55e";
}

// drawing functions
const ICON_CHARS: Record<string, string> = {
  initial: "\u25C7",
  cell_click: "", // drawn as image
  click: "",
  cell_keypress: "\u2328",
  keypress: "\u2328",
  clear: "\u21BA",
  attempt_solve: "\u2713",
  attempt_solve_success: "\u2713",
  attempt_solve_fail: "\u2717",
};

function draw_status_segment(ctx: CanvasRenderingContext2D, x: number, color: string) {
  const s = S.value;
  ctx.fillStyle = color;
  ctx.fillRect(x, 0, s.slot, s.statusBar);
}

function draw_baseline(ctx: CanvasRenderingContext2D, width: number) {
  const s = S.value;
  ctx.strokeStyle = "#d1d5db";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, s.tickY);
  ctx.lineTo(width, s.tickY);
  ctx.stroke();
}

function draw_tick(ctx: CanvasRenderingContext2D, x: number, major: boolean) {
  const s = S.value;
  ctx.strokeStyle = major ? "#374151" : "#e5e7eb";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, s.tickY);
  ctx.lineTo(x, s.tickY - s.tickH);
  ctx.stroke();
}

function draw_event_icon(ctx: CanvasRenderingContext2D, x: number, action: string, is_past: boolean) {
  const s = S.value;
  const is_image = (action === "cell_click" || action === "click") && mouse_left_img.complete;

  if (is_image) {
    ctx.globalAlpha = is_past ? 1 : 0.3;
    ctx.drawImage(mouse_left_img, x - s.iconSize / 2, s.iconY - s.iconSize / 2, s.iconSize, s.iconSize);
    ctx.globalAlpha = 1;
  } else {
    ctx.fillStyle = is_past ? "#374151" : "#d1d5db";
    ctx.fillText(ICON_CHARS[action] ?? "\u00B7", x, s.iconY);
  }
}

function draw_playhead(ctx: CanvasRenderingContext2D, x: number) {
  const s = S.value;
  const tri = props.size === "small" ? 3 : 5;
  const line_width = props.size === "small" ? 1 : 2;

  ctx.strokeStyle = "#2563eb";
  ctx.lineWidth = line_width;
  ctx.beginPath();
  ctx.moveTo(x, 0);
  ctx.lineTo(x, s.height);
  ctx.stroke();

  ctx.fillStyle = "#2563eb";
  ctx.beginPath();
  ctx.moveTo(x - tri, 0);
  ctx.lineTo(x + tri, 0);
  ctx.lineTo(x, tri + 2);
  ctx.closePath();
  ctx.fill();
}

// main draw callable
function draw() {
  const canvas = canvas_ref.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const s = S.value;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas_width.value;

  canvas.width = w * dpr;
  canvas.height = s.height * dpr;
  canvas.style.width = w + "px";
  canvas.style.height = s.height + "px";
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, s.height);

  const frames = props.frames;
  const current = props.current_frame;

  // status bar
  for (let i = 0; i < frames.length; i++) {
    const color = get_status_color(frames[i].action);
    if (color !== "transparent") draw_status_segment(ctx, i * s.slot, color);
  }

  // baseline + ticks
  draw_baseline(ctx, w);
  for (let i = 0; i < frames.length; i++) {
    draw_tick(ctx, i * s.slot + s.slot / 2, i % 5 === 0);
  }

  // icons
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.font = `${s.font} sans-serif`;
  for (let i = 0; i < frames.length; i++) {
    draw_event_icon(ctx, i * s.slot + s.slot / 2, frames[i].action, i <= current);
  }

  draw_playhead(ctx, (current + 1) * s.slot);
}

function frame_from_x(client_x: number): number {
  if (!container_ref.value) return 0;
  const rect = container_ref.value.getBoundingClientRect();
  const x = client_x - rect.left + container_ref.value.scrollLeft;
  const frame = Math.round(x / S.value.slot) - 1;
  return Math.max(0, Math.min(props.frames.length - 1, frame));
}

const PADDING_SLOTS = 3;

function scroll_to_current() {
  if (!container_ref.value) return;
  const container = container_ref.value;
  const slot = S.value.slot;
  const playhead_x = (props.current_frame + 1) * slot;
  const padding = PADDING_SLOTS * slot;
  const total_width = canvas_width.value;

  // keep padding slots visible ahead/behind, but allow scrolling to the very end
  const min_visible = playhead_x - container.clientWidth + padding;
  const max_visible = playhead_x - padding;

  if (container.scrollLeft > max_visible) {
    container.scrollLeft = Math.max(0, max_visible);
  } else if (container.scrollLeft < min_visible) {
    container.scrollLeft = Math.min(total_width - container.clientWidth, min_visible);
  }
}

function handle_mousedown(event: MouseEvent) {
  is_dragging.value = true;
  emit("seek", frame_from_x(event.clientX));
  document.addEventListener("mousemove", handle_mousemove);
  document.addEventListener("mouseup", handle_mouseup);
}

function handle_mousemove(event: MouseEvent) {
  if (!is_dragging.value) return;
  emit("seek", frame_from_x(event.clientX));
}

function handle_mouseup() {
  is_dragging.value = false;
  document.removeEventListener("mousemove", handle_mousemove);
  document.removeEventListener("mouseup", handle_mouseup);
}

// redraw on any change
watch(
  [() => props.frames, () => props.current_frame, () => props.is_playing],
  () => {
    draw();
    scroll_to_current();
  },
  { flush: "post" },
);

function handle_keydown(event: KeyboardEvent) {
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    if (props.current_frame > 0) emit("seek", props.current_frame - 1);
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    if (props.current_frame < props.frames.length - 1) emit("seek", props.current_frame + 1);
  } else if (event.key === " ") {
    event.preventDefault();
    emit("toggle-play");
  }
}

onMounted(() => {
  draw();
  document.addEventListener("keydown", handle_keydown);
});

onUnmounted(() => {
  document.removeEventListener("mousemove", handle_mousemove);
  document.removeEventListener("mouseup", handle_mouseup);
  document.removeEventListener("keydown", handle_keydown);
});
</script>

<template>
  <div class="flex items-center gap-2">
    <!-- play/pause button -->
    <button
      class="shrink-0 flex items-center justify-center rounded border border-gray-300 hover:bg-gray-100"
      :class="size === 'small' ? 'w-5 h-5 text-[10px]' : 'w-7 h-7 text-sm'"
      @click="emit('toggle-play')"
    >
      {{ is_playing ? "\u23F8" : "\u25B6" }}
    </button>

    <!-- scrollable canvas container -->
    <div
      ref="container_ref"
      class="flex-1 overflow-x-hidden cursor-pointer select-none border border-gray-200 rounded"
      @mousedown="handle_mousedown"
    >
      <canvas ref="canvas_ref" />
    </div>

    <!-- speed dropdown (hidden in small mode) -->
    <select
      v-if="size !== 'small'"
      class="shrink-0 text-xs text-gray-500 border border-gray-200 rounded px-1 py-1 bg-white cursor-pointer"
      :value="moves_per_second"
      @change="emit('set-mps', Number(($event.target as HTMLSelectElement).value))"
    >
      <option v-for="mps in MPS_OPTIONS" :key="mps" :value="mps">{{ mps }} mps</option>
    </select>

    <!-- frame counter (hidden in small mode) -->
    <span v-if="size !== 'small'" class="shrink-0 text-xs text-gray-400 tabular-nums whitespace-nowrap">
      {{ current_frame }}/{{ frames.length - 1 }}
    </span>
  </div>
</template>

<style scoped>
div::-webkit-scrollbar {
  height: 4px;
}
div::-webkit-scrollbar-track {
  background: transparent;
}
div::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}
</style>

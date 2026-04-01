<script setup lang="ts">
/**
 * Difficulty score vs min actions scatter plot.
 * Shows if the model's difficulty rating correlates with structural complexity.
 * Each dot is one puzzle, colored by type.
 */
import { ref, onMounted, nextTick } from "vue";
import * as d3 from "d3";
import Container from "@/core/components/ui/Container.vue";
import { api } from "@/core/services/client";
import PuzzleTypeSelector from "./PuzzleTypeSelector.vue";

const TYPE_COLORS: Record<string, string> = {
  aquarium: "#22d3ee",
  kakurasu: "#a3e635",
  lightup: "#fbbf24",
  minesweeper: "#4ade80",
  mosaic: "#e879f9",
  nonograms: "#f87171",
  norinori: "#f472b6",
  sudoku: "#60a5fa",
  tents: "#2dd4bf",
};

const container_el = ref<HTMLElement>();
const loading = ref(false);
const error = ref<string | null>(null);
const count = ref(0);
const show_all = ref(true);

const filter = ref({ puzzle_type: "", puzzle_size: "", puzzle_difficulty: "" });

function on_filter_update(value: { puzzle_type: string; puzzle_size: string; puzzle_difficulty: string }) {
  filter.value = value;
  if (!show_all.value) render();
}

function toggle_all() {
  show_all.value = !show_all.value;
  render();
}

onMounted(() => nextTick(render));

async function render() {
  if (!container_el.value) return;
  loading.value = true;
  error.value = null;
  count.value = 0;

  d3.select(container_el.value).selectAll("*").remove();

  try {
    const params: any = {};
    if (!show_all.value) {
      params.puzzle_type = filter.value.puzzle_type;
      if (filter.value.puzzle_size) params.puzzle_size = filter.value.puzzle_size;
      if (filter.value.puzzle_difficulty) params.puzzle_difficulty = filter.value.puzzle_difficulty;
    }

    const { data, error: err } = await api.GET("/api/puzzle/graphs/difficulty-vs-min-actions" as any, {
      params: { query: params },
    });

    if (err) {
      error.value = (err as any)?.detail || "Query failed";
      return;
    }

    const points: { puzzle_type: string; min_actions: number; difficulty: number }[] = (data as any)?.points ?? [];
    if (!points.length) {
      error.value = "No data found";
      return;
    }

    count.value = points.length;

    const margin = { top: 10, right: 20, bottom: 40, left: 55 };
    const width = container_el.value.clientWidth - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    const x = d3.scaleLinear()
      .domain([0, d3.max(points, (d) => d.difficulty) ?? 1])
      .nice()
      .range([0, width]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(points, (d) => d.min_actions) ?? 50])
      .nice()
      .range([height, 0]);

    const svg = d3.select(container_el.value)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // tooltip
    const tooltip = d3.select(container_el.value)
      .append("div")
      .style("display", "none")
      .style("position", "absolute")
      .style("background", "rgba(0,0,0,0.85)")
      .style("color", "#fff")
      .style("padding", "4px 8px")
      .style("border-radius", "4px")
      .style("font-size", "11px")
      .style("pointer-events", "none")
      .style("white-space", "nowrap");

    // dots
    svg.selectAll("circle")
      .data(points)
      .enter()
      .append("circle")
      .attr("cx", (d) => x(d.difficulty))
      .attr("cy", (d) => y(d.min_actions))
      .attr("r", 3)
      .attr("fill", (d) => TYPE_COLORS[d.puzzle_type] ?? "#888")
      .attr("opacity", 0.6)
      .on("mouseover", (event, d) => {
        tooltip
          .style("display", "block")
          .html(`<strong>${d.puzzle_type}</strong><br>difficulty: ${d.difficulty}<br>min actions: ${d.min_actions}`);
      })
      .on("mousemove", (event) => {
        tooltip
          .style("left", (event.offsetX + 12) + "px")
          .style("top", (event.offsetY - 10) + "px");
      })
      .on("mouseout", () => tooltip.style("display", "none"));

    // x axis
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(8))
      .selectAll("text")
      .attr("font-size", "10px");

    // y axis
    svg.append("g")
      .call(d3.axisLeft(y).ticks(8))
      .selectAll("text")
      .attr("font-size", "10px");

    // x label
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", height + 35)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#888")
      .text("Difficulty Score (model)");

    // y label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -40)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#888")
      .text("Min Actions");

    // legend (when showing all types)
    if (show_all.value) {
      const types = [...new Set(points.map((p) => p.puzzle_type))];
      const legend = svg.append("g").attr("transform", `translate(${width - 90}, 0)`);
      types.forEach((t, i) => {
        legend.append("circle").attr("cx", 0).attr("cy", i * 14).attr("r", 4).attr("fill", TYPE_COLORS[t] ?? "#888");
        legend.append("text").attr("x", 8).attr("y", i * 14 + 4).attr("font-size", "9px").attr("fill", "#666").text(t);
      });
    }

  } catch (e: any) {
    error.value = e.message || "Failed to load";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <Container>
    <div class="flex items-start justify-between mb-2">
      <div>
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Difficulty vs Min Actions</div>
        <p v-if="count" class="text-xs text-gray-400">{{ count.toLocaleString() }} puzzles</p>
      </div>
      <div class="flex gap-2 items-center">
        <button
          class="text-xs px-2 py-1 rounded border transition-colors"
          :class="show_all ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300'"
          @click="toggle_all"
        >
          All Types
        </button>
        <PuzzleTypeSelector v-if="!show_all" puzzle-type="minesweeper" @update="on_filter_update" />
      </div>
    </div>

    <div v-if="error" class="text-red-600 text-sm bg-red-50 p-3 rounded mb-2">
      {{ error }}
    </div>

    <div ref="container_el" class="w-full relative" />
  </Container>
</template>

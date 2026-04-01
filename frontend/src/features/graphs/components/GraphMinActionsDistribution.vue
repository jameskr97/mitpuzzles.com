<script setup lang="ts">
/**
 * Min actions distribution histogram.
 * Shows how many minimum clicks each puzzle requires.
 * Helps identify puzzles that are trivially easy (1-2 min actions).
 */
import { ref, onMounted, nextTick } from "vue";
import * as d3 from "d3";
import Container from "@/core/components/ui/Container.vue";
import { api } from "@/core/services/client";
import PuzzleTypeSelector from "./PuzzleTypeSelector.vue";

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

    const { data, error: err } = await api.GET("/api/puzzle/graphs/min-actions-distribution" as any, {
      params: { query: params },
    });

    if (err) {
      error.value = (err as any)?.detail || "Query failed";
      return;
    }

    const values: { puzzle_type: string; min_actions: number }[] = (data as any)?.values ?? [];
    if (!values.length) {
      error.value = "No data found";
      return;
    }

    count.value = values.length;
    const all_actions = values.map((v) => v.min_actions);

    const margin = { top: 10, right: 20, bottom: 35, left: 50 };
    const width = container_el.value.clientWidth - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;

    const max_val = d3.max(all_actions) ?? 50;

    const x = d3.scaleLinear()
      .domain([0, max_val])
      .nice()
      .range([0, width]);

    const bins = d3.bin()
      .domain(x.domain() as [number, number])
      .thresholds(x.ticks(Math.min(max_val, 40)))(all_actions);

    const y = d3.scaleLinear()
      .domain([0, d3.max(bins, (d) => d.length) ?? 0])
      .nice()
      .range([height, 0]);

    const svg = d3.select(container_el.value)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // bars
    svg.selectAll("rect")
      .data(bins)
      .enter()
      .append("rect")
      .attr("x", (d) => x(d.x0 ?? 0) + 1)
      .attr("y", (d) => y(d.length))
      .attr("width", (d) => Math.max(0, x(d.x1 ?? 0) - x(d.x0 ?? 0) - 1))
      .attr("height", (d) => height - y(d.length))
      .attr("fill", "#f59e0b")
      .attr("opacity", 0.8)
      .append("title")
      .text((d) => `${d.x0?.toFixed(0)}–${d.x1?.toFixed(0)} min actions: ${d.length} puzzles`);

    // highlight low-action puzzles
    const low_count = all_actions.filter((a) => a <= 3).length;
    if (low_count > 0) {
      svg.append("text")
        .attr("x", x(3) + 8)
        .attr("y", 15)
        .attr("font-size", "10px")
        .attr("fill", "#ef4444")
        .text(`${low_count} puzzles with ≤3 min actions`);

      svg.append("line")
        .attr("x1", x(3))
        .attr("x2", x(3))
        .attr("y1", 0)
        .attr("y2", height)
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 1.5)
        .attr("stroke-dasharray", "4,3");
    }

    // x axis
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(10))
      .selectAll("text")
      .attr("font-size", "10px");

    // y axis
    svg.append("g")
      .call(d3.axisLeft(y).ticks(6))
      .selectAll("text")
      .attr("font-size", "10px");

    // x label
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", height + 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#888")
      .text("Min Actions");

    // y label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -35)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#888")
      .text("Puzzles");

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
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Min Actions Distribution</div>
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

    <div ref="container_el" class="w-full" />
  </Container>
</template>

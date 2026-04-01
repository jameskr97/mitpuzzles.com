<script setup lang="ts">
/**
 * Solve time distribution histogram.
 * Shows a histogram of solve times for a given puzzle type/size/difficulty.
 * Uses D3 for binning and rendering.
 */
import { ref } from "vue";
import * as d3 from "d3";
import Container from "@/core/components/ui/Container.vue";
import { api } from "@/core/services/client";
import PuzzleTypeSelector from "./PuzzleTypeSelector.vue";

const container = ref<HTMLElement>();
const loading = ref(false);
const error = ref<string | null>(null);
const count = ref(0);

const filter = ref({ puzzle_type: "", puzzle_size: "", puzzle_difficulty: "" });

function on_filter_update(value: { puzzle_type: string; puzzle_size: string; puzzle_difficulty: string }) {
  filter.value = value;
  render();
}

async function render() {
  if (!container.value) return;
  loading.value = true;
  error.value = null;
  count.value = 0;

  d3.select(container.value).selectAll("*").remove();

  try {
    const params: any = { puzzle_type: filter.value.puzzle_type };
    if (filter.value.puzzle_size) params.puzzle_size = filter.value.puzzle_size;
    if (filter.value.puzzle_difficulty) params.puzzle_difficulty = filter.value.puzzle_difficulty;

    const { data, error: err } = await api.GET("/api/puzzle/graphs/solve-times" as any, {
      params: { query: params },
    });

    if (err) {
      error.value = (err as any)?.detail || "Query failed";
      return;
    }

    const times: number[] = (data as any)?.times ?? [];
    if (!times.length) {
      error.value = "No solve data found";
      return;
    }

    count.value = times.length;

    // dimensions
    const margin = { top: 10, right: 20, bottom: 35, left: 50 };
    const width = container.value.clientWidth - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;

    // scales
    const x = d3.scaleLinear()
      .domain([0, d3.quantile(times.sort(d3.ascending), 0.95) ?? d3.max(times) ?? 100])
      .nice()
      .range([0, width]);

    const bins = d3.bin()
      .domain(x.domain() as [number, number])
      .thresholds(x.ticks(40))(times);

    const y = d3.scaleLinear()
      .domain([0, d3.max(bins, (d) => d.length) ?? 0])
      .nice()
      .range([height, 0]);

    // svg
    const svg = d3.select(container.value)
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
      .attr("fill", "#3b82f6")
      .attr("opacity", 0.8)
      .append("title")
      .text((d) => `${d.x0?.toFixed(0)}–${d.x1?.toFixed(0)}s: ${d.length} solves`);

    // x axis
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(10).tickFormat((d) => `${d}s`))
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
      .text("Solve Time (seconds)");

    // y label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -35)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px")
      .attr("fill", "#888")
      .text("Solves");

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
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Solve Time Distribution</div>
        <p v-if="count" class="text-xs text-gray-400">{{ count.toLocaleString() }} solves (95th percentile cutoff)</p>
      </div>
      <PuzzleTypeSelector puzzle-type="minesweeper" @update="on_filter_update" />
    </div>

    <div v-if="error" class="text-red-600 text-sm bg-red-50 p-3 rounded mb-2">
      {{ error }}
    </div>

    <div ref="container" class="w-full" />
  </Container>
</template>

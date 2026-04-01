<script setup lang="ts">
/**
 * Click order heatmap.
 * For a specific puzzle, shows the average order in which cells were first clicked
 * across all solved attempts. Early clicks = cool colors, late clicks = warm colors.
 * Null cells (immutable/never clicked) are gray.
 */
import { ref, watch, onMounted } from "vue";
import * as d3 from "d3";
import Container from "@/core/components/ui/Container.vue";
import { Button } from "@/core/components/ui/button";

const props = defineProps<{
  puzzleId: string;
}>();

const container = ref<HTMLElement>();
const loading = ref(false);
const error = ref<string | null>(null);
const attempt_count = ref(0);

async function render() {
  if (!container.value) return;
  loading.value = true;
  error.value = null;

  d3.select(container.value).selectAll("*").remove();

  try {
    const res = await fetch(`/api/puzzle/graphs/puzzle/${props.puzzleId}/click-order`, {
      credentials: "include",
    });
    if (!res.ok) {
      error.value = `Failed: ${res.status}`;
      return;
    }

    const data = await res.json();
    const { rows, cols, heatmap } = data;
    attempt_count.value = data.attempt_count;

    if (!heatmap.length) {
      error.value = "No solve data available";
      return;
    }

    // find min/max rank for color scale
    let min_rank = Infinity;
    let max_rank = -Infinity;
    for (const row of heatmap) {
      for (const val of row) {
        if (val !== null) {
          min_rank = Math.min(min_rank, val);
          max_rank = Math.max(max_rank, val);
        }
      }
    }

    const container_width = container.value.clientWidth;
    const cell_size = Math.floor(Math.min(container_width / cols, 400 / rows));
    const width = cell_size * cols;
    const height = cell_size * rows;
    const margin = { top: 0, right: 80, bottom: 0, left: 0 };

    // color: early = blue, late = red
    const color = d3.scaleSequential(d3.interpolateRdYlBu)
      .domain([max_rank, min_rank]); // reversed so blue = early, red = late

    const svg = d3.select(container.value)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // tooltip
    const tooltip = d3.select(container.value)
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

    // cells
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = heatmap[r][c];
        svg.append("rect")
          .attr("x", c * cell_size)
          .attr("y", r * cell_size)
          .attr("width", cell_size - 1)
          .attr("height", cell_size - 1)
          .attr("fill", val !== null ? color(val) : "#e5e7eb")
          .attr("rx", 2)
          .on("mouseover", (event) => {
            tooltip
              .style("display", "block")
              .html(val !== null ? `Cell (${r},${c})<br>Avg rank: <strong>${val}</strong>` : `Cell (${r},${c})<br>Not clicked`);
          })
          .on("mousemove", (event) => {
            tooltip
              .style("left", (event.offsetX + 12) + "px")
              .style("top", (event.offsetY - 10) + "px");
          })
          .on("mouseout", () => tooltip.style("display", "none"));

        // label
        if (val !== null && cell_size >= 20) {
          svg.append("text")
            .attr("x", c * cell_size + cell_size / 2)
            .attr("y", r * cell_size + cell_size / 2 + 1)
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "central")
            .attr("font-size", Math.min(cell_size * 0.4, 12) + "px")
            .attr("fill", val < (min_rank + max_rank) / 2 ? "#fff" : "#333")
            .text(val.toFixed(1));
        }
      }
    }

    // legend
    const legend_height = height;
    const legend_width = 15;
    const legend_x = width + 20;

    const legend_scale = d3.scaleLinear()
      .domain([min_rank, max_rank])
      .range([0, legend_height]);

    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
      .attr("id", "click-order-gradient")
      .attr("x1", "0%").attr("y1", "0%")
      .attr("x2", "0%").attr("y2", "100%");
    gradient.append("stop").attr("offset", "0%").attr("stop-color", color(min_rank));
    gradient.append("stop").attr("offset", "100%").attr("stop-color", color(max_rank));

    svg.append("rect")
      .attr("x", legend_x)
      .attr("y", 0)
      .attr("width", legend_width)
      .attr("height", legend_height)
      .style("fill", "url(#click-order-gradient)");

    svg.append("text")
      .attr("x", legend_x + legend_width + 4)
      .attr("y", 10)
      .attr("font-size", "9px")
      .attr("fill", "#888")
      .text("early");

    svg.append("text")
      .attr("x", legend_x + legend_width + 4)
      .attr("y", legend_height - 2)
      .attr("font-size", "9px")
      .attr("fill", "#888")
      .text("late");

  } catch (e: any) {
    error.value = e.message || "Failed to load";
  } finally {
    loading.value = false;
  }
}

onMounted(render);
watch(() => props.puzzleId, render);
</script>

<template>
  <Container>
    <div class="flex items-start justify-between mb-2">
      <div>
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Click Order Heatmap</div>
        <p v-if="attempt_count" class="text-xs text-gray-400">Averaged across {{ attempt_count }} solves</p>
      </div>
      <Button size="sm" :disabled="loading" @click="render">
        {{ loading ? "..." : "Refresh" }}
      </Button>
    </div>

    <div v-if="error" class="text-red-600 text-sm bg-red-50 p-3 rounded mb-2">
      {{ error }}
    </div>

    <div ref="container" class="w-full relative" />
  </Container>
</template>

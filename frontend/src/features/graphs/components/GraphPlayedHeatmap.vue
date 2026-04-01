<script setup lang="ts">
/**
 * played game heatmap
 * I added this because I wanted to see, of all the games we added to the database,
 * which ones have/haven't been played and which ones have been played the most.
 *
 * every puzzle in the database is shown as a cell in a grid.
 * - color: puzzle type
 * - brightness: number of plays.
 * - black: never played.
 * sorted by play count descending (most played at top, unplayed at bottom).
 */

import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import * as d3 from "d3";
import Container from "@/core/components/ui/Container.vue";
import { Button } from "@/core/components/ui/button";

const router = useRouter();
import { api } from "@/core/services/client";

const props = withDefaults(
  defineProps<{
    cellSize?: number;
    hideUnplayed?: boolean;
    completedOnly?: boolean;
  }>(),
  {
    cellSize: 6,
    hideUnplayed: false,
    completedOnly: false,
  },
);

const container = ref<HTMLElement>();
const loading = ref(false);
const error = ref<string | null>(null);

// [dark, bright] — wide range for clear contrast
const TYPE_HUES: Record<string, [string, string]> = {
  aquarium: ["#164e63", "#22d3ee"],
  battleships: ["#7c2d12", "#fb923c"],
  hashi: ["#4c1d95", "#a78bfa"],
  kakurasu: ["#365314", "#a3e635"],
  lightup: ["#78350f", "#fbbf24"],
  minesweeper: ["#14532d", "#4ade80"],
  mosaic: ["#701a75", "#e879f9"],
  nonograms: ["#7f1d1d", "#f87171"],
  norinori: ["#831843", "#f472b6"],
  sudoku: ["#1e3a5f", "#60a5fa"],
  tents: ["#134e4a", "#2dd4bf"],
};

async function render() {
  if (!container.value) return;
  loading.value = true;
  error.value = null;

  d3.select(container.value).selectAll("*").remove();

  try {
    const { data, error: err } = await api.GET("/api/puzzle/graphs/puzzle-heatmap" as any, {
      params: { query: { has_attempts: props.hideUnplayed, completed_only: props.completedOnly } },
    });

    if (err) {
      error.value = (err as any)?.detail || "Query failed";
      return;
    }

    const rows = data as any as {
      id: string;
      puzzle_type: string;
      puzzle_size: string;
      puzzle_difficulty: string;
      play_count: number;
    }[];
    if (!rows.length) {
      error.value = "No puzzles found";
      return;
    }

    const max_plays = d3.max(rows, (d) => d.play_count) ?? 1;

    const cell_size = props.cellSize;
    const cell_gap = 0;
    const step = cell_size + cell_gap;
    const container_width = container.value.clientWidth;
    const cols_per_row = Math.floor(container_width / step);

    function color(puzzle_type: string, play_count: number): string {
      if (play_count === 0) return "#0a0a0a";
      const [dark, bright] = TYPE_HUES[puzzle_type] ?? ["#1a1a1a", "#a3a3a3"];
      const t = Math.min(play_count / max_plays, 1);
      const opacity = 0.3 + t * 0.7; // 30% at lowest, 100% at highest
      const rgb = d3.interpolateRgb(bright, dark)(t);
      const c = d3.color(rgb);
      if (c) c.opacity = opacity;
      return c?.toString() ?? rgb;
    }

    rows.sort((a, b) => b.play_count - a.play_count);

    const by_type = d3.group(rows, (d) => d.puzzle_type);
    const total_rows = Math.ceil(rows.length / cols_per_row);

    const types = [...by_type.keys()];
    const swatch_size = 10;
    const swatch_gap = 6;
    const legend_height = swatch_size + 12;

    const svg = d3
      .select(container.value)
      .append("svg")
      .attr("width", container_width)
      .attr("height", legend_height + total_rows * step + 10);

    let legend_x = 0;
    for (const t of types) {
      const [, bright] = TYPE_HUES[t] ?? ["#a3a3a3", "#e5e5e5"];
      svg
        .append("rect")
        .attr("x", legend_x)
        .attr("y", 0)
        .attr("width", swatch_size)
        .attr("height", swatch_size)
        .attr("fill", bright)
        .attr("rx", 2);

      svg
        .append("text")
        .attr("x", legend_x + swatch_size + 3)
        .attr("y", swatch_size - 1)
        .attr("font-size", "10px")
        .attr("fill", "#666")
        .text(t);

      legend_x += swatch_size + 3 + t.length * 6 + swatch_gap + 8;
    }

    // tooltip
    const tooltip = d3
      .select(container.value)
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

    const g = svg.append("g").attr("transform", `translate(0, ${legend_height})`);

    g.selectAll("rect")
      .data(rows)
      .enter()
      .append("rect")
      .attr("x", (_, i) => (i % cols_per_row) * step)
      .attr("y", (_, i) => Math.floor(i / cols_per_row) * step)
      .attr("width", cell_size)
      .attr("height", cell_size)
      .attr("fill", (d) => color(d.puzzle_type, d.play_count))
      .attr("stroke", "#333")
      .attr("stroke-width", 0.5)
      .attr("cursor", "pointer")
      .on("click", (_, d) => router.push({ name: "puzzle-detail", params: { puzzle_id: d.id } }))
      .on("mouseover", (event, d) => {
        tooltip
          .style("display", "block")
          .html(
            `<strong>${d.puzzle_type}</strong> ${d.puzzle_size} ${d.puzzle_difficulty ?? ""}<br>${d.play_count} plays`,
          );
      })
      .on("mousemove", (event) => {
        tooltip.style("left", event.offsetX + 12 + "px").style("top", event.offsetY - 10 + "px");
      })
      .on("mouseout", () => {
        tooltip.style("display", "none");
      });

    svg.attr("height", legend_height + total_rows * step + 10);
  } catch (e: any) {
    error.value = e.message || "Failed to load";
  } finally {
    loading.value = false;
  }
}

onMounted(render);
</script>

<template>
  <Container>
    <div class="flex items-start justify-between mb-1">
      <div>
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Puzzle Play Heatmap</div>
        <p class="text-sm text-gray-500">Every puzzle as a cell. Darker = more plays. Black = never played.</p>
        <p class="text-sm text-gray-500">
          Includes puzzles that a user interacted with/attempted, but did not actually finish. Detail pages may present
          with less games than expected.
        </p>
      </div>
      <Button size="sm" :disabled="loading" @click="render">
        {{ loading ? "Loading..." : "Refresh" }}
      </Button>
    </div>

    <div v-if="error" class="text-red-600 text-sm bg-red-50 p-3 rounded mb-2">
      {{ error }}
    </div>

    <div ref="container" class="w-full overflow-x-auto relative" />
  </Container>
</template>

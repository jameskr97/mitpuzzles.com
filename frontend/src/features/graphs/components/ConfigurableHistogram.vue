<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import * as d3 from "d3";
import type { ChartFeature } from "./ConfigurableChart.vue";

const props = withDefaults(defineProps<{
  points: Record<string, any>[];
  features: ChartFeature[];
  /** Lock to this feature key */
  feature?: string;
  /** Default feature selection (still changeable) */
  defaultFeature?: string;
  /** Number of bins */
  bins?: number;
  /** Use 95th percentile cutoff */
  percentileCutoff?: boolean;
  /** Bar color */
  color?: string;
  /** Chart height in pixels */
  height?: number;
}>(), {
  bins: 40,
  percentileCutoff: true,
  color: "#6366f1",
  height: 256,
});

const svg_ref = ref<SVGSVGElement | null>(null);
const container_ref = ref<HTMLDivElement | null>(null);
const width = ref(500);
const selected_feature = ref(props.feature ?? props.defaultFeature ?? props.features[0]?.key ?? "");
const locked = computed(() => !!props.feature);
const active_feature = computed(() => props.features.find(f => f.key === selected_feature.value));

const margin = { top: 12, right: 16, bottom: 36, left: 52 };

function render() {
  if (!svg_ref.value) return;

  const svg = d3.select(svg_ref.value);
  svg.selectAll("*").remove();

  // clean up old tooltip
  if (container_ref.value) {
    d3.select(container_ref.value).selectAll("div[style*='position: absolute']").remove();
  }

  const w = width.value;
  const h = props.height;
  const inner_w = w - margin.left - margin.right;
  const inner_h = h - margin.top - margin.bottom;
  if (inner_w <= 0 || inner_h <= 0) return;

  const feat = active_feature.value;
  if (!feat) return;

  const raw_values: number[] = props.points
    .map(p => p[feat.key])
    .filter(v => v != null && typeof v === "number");

  if (raw_values.length === 0) return;

  const sorted = [...raw_values].sort(d3.ascending);
  const max_val = props.percentileCutoff
    ? (d3.quantile(sorted, 0.95) ?? d3.max(sorted) ?? 100)
    : (d3.max(sorted) ?? 100);

  const values = props.percentileCutoff ? sorted.filter(v => v <= max_val) : sorted;

  const g = svg
    .attr("width", w)
    .attr("height", h)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleLinear()
    .domain([0, max_val])
    .nice()
    .range([0, inner_w]);

  const histogram = d3.bin()
    .domain(x.domain() as [number, number])
    .thresholds(x.ticks(props.bins))(values);

  const y = d3.scaleLinear()
    .domain([0, d3.max(histogram, d => d.length) ?? 0])
    .nice()
    .range([inner_h, 0]);

  // Grid
  g.append("g")
    .selectAll("line")
    .data(y.ticks())
    .join("line")
    .attr("x1", 0)
    .attr("x2", inner_w)
    .attr("y1", d => y(d))
    .attr("y2", d => y(d))
    .attr("stroke", "#f3f4f6")
    .attr("stroke-width", 1);

  // Tooltip
  const tooltip = d3.select(container_ref.value)
    .append("div")
    .style("position", "absolute")
    .style("pointer-events", "none")
    .style("background", "rgba(0,0,0,0.8)")
    .style("color", "white")
    .style("padding", "4px 8px")
    .style("border-radius", "4px")
    .style("font-size", "11px")
    .style("opacity", 0)
    .style("z-index", 10);

  const fmt = feat.format ?? ((v: number) => v.toLocaleString());

  // Bars
  g.selectAll("rect")
    .data(histogram)
    .join("rect")
    .attr("x", d => x(d.x0 ?? 0) + 1)
    .attr("y", d => y(d.length))
    .attr("width", d => Math.max(0, x(d.x1 ?? 0) - x(d.x0 ?? 0) - 1))
    .attr("height", d => inner_h - y(d.length))
    .attr("fill", props.color)
    .attr("opacity", 0.8)
    .on("mouseenter", (_event, d) => {
      tooltip
        .html(`${fmt(d.x0 ?? 0)} – ${fmt(d.x1 ?? 0)}<br>${d.length} solves`)
        .style("opacity", 1);
    })
    .on("mousemove", (event) => {
      const rect = container_ref.value!.getBoundingClientRect();
      tooltip
        .style("left", (event.clientX - rect.left + 12) + "px")
        .style("top", (event.clientY - rect.top - 10) + "px");
    })
    .on("mouseleave", () => {
      tooltip.style("opacity", 0);
    });

  // X axis
  const x_axis = d3.axisBottom(x).ticks(10);
  if (feat.format) x_axis.tickFormat(d => feat.format!(d as number));
  g.append("g")
    .attr("transform", `translate(0,${inner_h})`)
    .call(x_axis)
    .selectAll("text")
    .style("font-size", "10px");

  // Y axis
  g.append("g")
    .call(d3.axisLeft(y).ticks(6))
    .selectAll("text")
    .style("font-size", "10px");

  // X label
  g.append("text")
    .attr("x", inner_w / 2)
    .attr("y", inner_h + margin.bottom - 4)
    .attr("text-anchor", "middle")
    .style("font-size", "11px")
    .style("fill", "#9ca3af")
    .text(feat.label);

  // Y label
  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -inner_h / 2)
    .attr("y", -margin.left + 14)
    .attr("text-anchor", "middle")
    .style("font-size", "11px")
    .style("fill", "#9ca3af")
    .text("Count");
}

let resize_observer: ResizeObserver | null = null;

onMounted(() => {
  if (container_ref.value) {
    width.value = container_ref.value.clientWidth;
    resize_observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        width.value = entry.contentRect.width;
      }
    });
    resize_observer.observe(container_ref.value);
  }
  render();
});

onUnmounted(() => {
  resize_observer?.disconnect();
  if (container_ref.value) {
    d3.select(container_ref.value).selectAll("div[style*='position: absolute']").remove();
  }
});

watch([() => props.points, () => props.features, selected_feature, width], render, { deep: true });
</script>

<template>
  <div ref="container_ref" class="relative w-full">
    <div v-if="!locked" class="flex items-center gap-2 mb-2 text-xs">
      <label class="text-gray-500">Feature:</label>
      <select v-model="selected_feature" class="border border-gray-200 rounded px-1.5 py-0.5 text-xs bg-white">
        <option v-for="f in features" :key="f.key" :value="f.key">{{ f.label }}</option>
      </select>
    </div>
    <svg ref="svg_ref" :height="height" class="w-full" />
  </div>
</template>

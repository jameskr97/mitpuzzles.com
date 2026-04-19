<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import * as d3 from "d3";

export interface ChartFeature {
  key: string;
  label: string;
  type: "number" | "category";
  format?: (v: any) => string;
}

export interface ChartSeries {
  key: string;
  label: string;
  color: string;
}

const props = withDefaults(defineProps<{
  points: Record<string, any>[];
  features: ChartFeature[];
  /** Lock x-axis to this feature key */
  x?: string;
  /** Lock y-axis to this feature key */
  y?: string;
  /** Default x selection (still changeable) */
  defaultX?: string;
  /** Default y selection (still changeable) */
  defaultY?: string;
  /** Default color selection (still changeable) */
  defaultColor?: string;
  /** Optional series grouping (renders separate colored lines/dots) */
  series?: ChartSeries[];
  /** Field in data points that maps to series key */
  seriesKey?: string;
  /** Additional features available for color-by (e.g. category fields not in features) */
  colorFeatures?: ChartFeature[];
  /** Lock color to this feature key */
  colorBy?: string;
  /** Chart height in pixels */
  height?: number;
  /** Show as line chart instead of scatter */
  line?: boolean;
  /** Line tension (0 = straight, 0.4 = smooth) */
  tension?: number;
  /** Point radius */
  pointRadius?: number;
  /** Horizontal reference lines */
  referenceLines?: { value: number; label?: string; color?: string; dash?: string }[];
}>(), {
  height: 256,
  line: false,
  tension: 0.3,
  pointRadius: 3,
});

const svg_ref = ref<SVGSVGElement | null>(null);
const container_ref = ref<HTMLDivElement | null>(null);
const width = ref(500);
const selected_x = ref(props.x ?? props.defaultX ?? props.features[0]?.key ?? "");
const selected_y = ref(props.y ?? props.defaultY ?? props.features[1]?.key ?? props.features[0]?.key ?? "");
const selected_color = ref(props.colorBy ?? props.defaultColor ?? "");

const locked_x = computed(() => !!props.x);
const locked_y = computed(() => !!props.y);
const locked_color = computed(() => !!props.colorBy);
const has_series = computed(() => !!(props.series && props.seriesKey));
const show_color_picker = computed(() => !has_series.value && !locked_color.value);

const all_color_features = computed(() => [
  ...props.features,
  ...(props.colorFeatures ?? []),
]);

const x_feature = computed(() => props.features.find(f => f.key === selected_x.value));
const y_feature = computed(() => props.features.find(f => f.key === selected_y.value));
const color_feature = computed(() => all_color_features.value.find(f => f.key === selected_color.value));

const margin = { top: 12, right: 16, bottom: 36, left: 52 };

function format_value(feature: ChartFeature | undefined, value: any): string {
  if (!feature) return String(value);
  if (feature.format) return feature.format(value);
  if (typeof value === "number") return value.toLocaleString();
  return String(value);
}

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

  const g = svg
    .attr("width", w)
    .attr("height", h)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const xf = x_feature.value;
  const yf = y_feature.value;
  if (!xf || !yf) return;

  const all_x = props.points.map(p => p[xf.key]).filter(v => v != null);
  const all_y = props.points.map(p => p[yf.key]).filter(v => v != null);
  if (all_x.length === 0 || all_y.length === 0) return;

  // Scales
  const x_scale = d3.scaleLinear()
    .domain(d3.extent(all_x) as [number, number])
    .range([0, inner_w])
    .nice();

  const y_scale = d3.scaleLinear()
    .domain(d3.extent(all_y) as [number, number])
    .range([inner_h, 0])
    .nice();

  // Color scale
  const cf = color_feature.value;
  let get_color: (d: Record<string, any>) => string;

  if (has_series.value) {
    // Series-based coloring
    const series_map = new Map(props.series!.map(s => [s.key, s.color]));
    get_color = (d) => series_map.get(d[props.seriesKey!]) ?? "#6366f1";
  } else if (cf && cf.type === "category") {
    const unique_vals = [...new Set(props.points.map(p => p[cf.key]).filter(v => v != null))];
    const cat_scale = d3.scaleOrdinal(d3.schemeCategory10).domain(unique_vals.map(String));
    get_color = (d) => {
      const v = d[cf.key];
      return v != null ? cat_scale(String(v)) : "#9ca3af";
    };
  } else if (cf && cf.type === "number") {
    const color_vals = props.points.map(p => p[cf.key]).filter(v => v != null && typeof v === "number");
    const [c_min, c_max] = d3.extent(color_vals) as [number, number];
    const num_scale = d3.scaleSequential(d3.interpolateViridis).domain([c_min, c_max]);
    get_color = (d) => {
      const v = d[cf.key];
      return v != null ? num_scale(v) : "#9ca3af";
    };
  } else {
    get_color = () => "#6366f1";
  }

  // Axes
  const x_axis = d3.axisBottom(x_scale).ticks(Math.min(10, Math.floor(inner_w / 50)));
  const y_axis = d3.axisLeft(y_scale).ticks(Math.min(8, Math.floor(inner_h / 30)));

  if (xf.format) x_axis.tickFormat((d) => xf.format!(d as number));
  if (yf.format) y_axis.tickFormat((d) => yf.format!(d as number));

  g.append("g")
    .attr("transform", `translate(0,${inner_h})`)
    .call(x_axis)
    .selectAll("text")
    .style("font-size", "10px");

  g.append("g")
    .call(y_axis)
    .selectAll("text")
    .style("font-size", "10px");

  // Axis labels
  g.append("text")
    .attr("x", inner_w / 2)
    .attr("y", inner_h + margin.bottom - 4)
    .attr("text-anchor", "middle")
    .style("font-size", "11px")
    .style("fill", "#9ca3af")
    .text(xf.label);

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -inner_h / 2)
    .attr("y", -margin.left + 14)
    .attr("text-anchor", "middle")
    .style("font-size", "11px")
    .style("fill", "#9ca3af")
    .text(yf.label);

  // Grid lines
  g.append("g")
    .selectAll("line")
    .data(y_scale.ticks())
    .join("line")
    .attr("x1", 0)
    .attr("x2", inner_w)
    .attr("y1", d => y_scale(d))
    .attr("y2", d => y_scale(d))
    .attr("stroke", "#f3f4f6")
    .attr("stroke-width", 1);

  // Reference lines
  if (props.referenceLines) {
    for (const rl of props.referenceLines) {
      const y_pos = y_scale(rl.value);
      if (y_pos < 0 || y_pos > inner_h) continue;
      g.append("line")
        .attr("x1", 0).attr("x2", inner_w)
        .attr("y1", y_pos).attr("y2", y_pos)
        .attr("stroke", rl.color ?? "#9ca3af")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", rl.dash ?? "6,3");
      if (rl.label) {
        g.append("text")
          .attr("x", inner_w - 4).attr("y", y_pos - 4)
          .attr("text-anchor", "end")
          .style("font-size", "9px")
          .style("fill", rl.color ?? "#9ca3af")
          .text(rl.label);
      }
    }
  }

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

  // Group by series for lines, or render all points flat
  if (has_series.value) {
    const by_series = new Map<string, Record<string, any>[]>();
    for (const p of props.points) {
      const sk = p[props.seriesKey!];
      if (!by_series.has(sk)) by_series.set(sk, []);
      by_series.get(sk)!.push(p);
    }

    for (const s of props.series!) {
      const valid = (by_series.get(s.key) ?? []).filter(p => p[xf.key] != null && p[yf.key] != null);

      if (props.line && valid.length > 1) {
        const line_gen = d3.line<Record<string, any>>()
          .x(d => x_scale(d[xf.key]))
          .y(d => y_scale(d[yf.key]))
          .curve(props.tension > 0 ? d3.curveCatmullRom.alpha(props.tension) : d3.curveLinear);

        g.append("path")
          .datum(valid)
          .attr("d", line_gen)
          .attr("fill", "none")
          .attr("stroke", s.color)
          .attr("stroke-width", 2)
          .attr("opacity", 0.8);
      }
    }
  }

  // All points (flat, colored individually)
  const valid_points = props.points.filter(p => p[xf.key] != null && p[yf.key] != null);

  g.selectAll(".dot")
    .data(valid_points)
    .join("circle")
    .attr("cx", d => x_scale(d[xf.key]))
    .attr("cy", d => y_scale(d[yf.key]))
    .attr("r", props.pointRadius)
    .attr("fill", d => get_color(d))
    .attr("opacity", 0.7)
    .on("mouseenter", (event, d) => {
      const lines = [
        `${xf.label}: ${format_value(xf, d[xf.key])}`,
        `${yf.label}: ${format_value(yf, d[yf.key])}`,
      ];
      if (cf) lines.push(`${cf.label}: ${format_value(cf, d[cf.key])}`);
      tooltip.html(lines.join("<br>")).style("opacity", 1);
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

  // Legend for category color
  if (cf && cf.type === "category" && !has_series.value) {
    const unique_vals = [...new Set(props.points.map(p => p[cf.key]).filter(v => v != null))];
    const cat_scale = d3.scaleOrdinal(d3.schemeCategory10).domain(unique_vals.map(String));

    const legend_padding = 6;
    const row_height = 14;
    const legend_h = unique_vals.length * row_height + legend_padding * 2;

    const legend = g.append("g")
      .attr("transform", `translate(${inner_w - 10}, 0)`);

    // measure text widths to size the background
    const temp_texts = unique_vals.map(v => String(v));
    const max_text_w = Math.max(...temp_texts.map(t => t.length * 6), 30);
    const legend_w = max_text_w + 20 + legend_padding * 2;

    legend.append("rect")
      .attr("x", -legend_w + legend_padding)
      .attr("y", -legend_padding)
      .attr("width", legend_w)
      .attr("height", legend_h)
      .attr("rx", 4)
      .attr("fill", "white")
      .attr("opacity", 0.85);

    unique_vals.forEach((val, i) => {
      const row = legend.append("g").attr("transform", `translate(0, ${i * row_height + legend_padding})`);
      row.append("circle").attr("r", 4).attr("cx", 0).attr("cy", 0).attr("fill", cat_scale(String(val)));
      row.append("text").attr("x", -8).attr("y", 4).attr("text-anchor", "end").style("font-size", "9px").style("fill", "#6b7280").text(String(val));
    });
  }

  // legend for series mode
  if (has_series.value && props.series && props.series.length > 1) {
    const row_height = 14;
    const legend_padding = 6;
    const legend_h = props.series.length * row_height + legend_padding * 2;

    const legend = g.append("g")
      .attr("transform", `translate(${inner_w - 10}, 0)`);

    const max_text_w = Math.max(...props.series.map(s => s.label.length * 6), 30);
    const legend_w = max_text_w + 20 + legend_padding * 2;

    legend.append("rect")
      .attr("x", -legend_w + legend_padding)
      .attr("y", -legend_padding)
      .attr("width", legend_w)
      .attr("height", legend_h)
      .attr("rx", 4)
      .attr("fill", "white")
      .attr("opacity", 0.85);

    props.series.forEach((s, i) => {
      const row = legend.append("g").attr("transform", `translate(0, ${i * row_height + legend_padding})`);
      row.append("circle").attr("r", 4).attr("cx", 0).attr("cy", 0).attr("fill", s.color);
      row.append("text").attr("x", -8).attr("y", 4).attr("text-anchor", "end").style("font-size", "9px").style("fill", "#6b7280").text(s.label);
    });
  }
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

watch([() => props.points, () => props.features, () => props.series, selected_x, selected_y, selected_color, width], render, { deep: true });
</script>

<template>
  <div ref="container_ref" class="relative w-full">
    <div v-if="!locked_x || !locked_y || show_color_picker" class="flex items-center gap-2 mb-2 text-xs flex-wrap">
      <template v-if="!locked_x">
        <label class="text-gray-500">X:</label>
        <select v-model="selected_x" class="border border-gray-200 rounded px-1.5 py-0.5 text-xs bg-white">
          <option v-for="f in features" :key="f.key" :value="f.key">{{ f.label }}</option>
        </select>
      </template>
      <template v-if="!locked_y">
        <label class="text-gray-500">Y:</label>
        <select v-model="selected_y" class="border border-gray-200 rounded px-1.5 py-0.5 text-xs bg-white">
          <option v-for="f in features" :key="f.key" :value="f.key">{{ f.label }}</option>
        </select>
      </template>
      <template v-if="show_color_picker">
        <label class="text-gray-500">Color:</label>
        <select v-model="selected_color" class="border border-gray-200 rounded px-1.5 py-0.5 text-xs bg-white">
          <option value="">none</option>
          <option v-for="f in all_color_features" :key="f.key" :value="f.key">{{ f.label }}</option>
        </select>
      </template>
    </div>
    <svg ref="svg_ref" :height="height" class="w-full" />
  </div>
</template>

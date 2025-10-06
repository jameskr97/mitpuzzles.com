/**
 * Generic composable for gutter marking functionality
 * Allows users to click gutters to toggle between normal and faded states
 * to mark completed sections in puzzle games
 */
import { ref, computed } from "vue";
import { usePuzzleProgressStore } from "@/store/puzzle/usePuzzleProgressStore";

export interface GutterMarkings {
  top?: boolean[];
  left?: boolean[];
  right?: boolean[];
  bottom?: boolean[];
}

export function useGutterMarking(puzzle_type: string, gutter_sizes: {
  top?: number;
  left?: number;
  right?: number;
  bottom?: number;
}) {
  const progress_store = usePuzzleProgressStore();

  // initialize marking arrays based on gutter sizes
  const initialize_markings = (): GutterMarkings => {
    const markings: GutterMarkings = {};
    if (gutter_sizes.top) markings.top = new Array(gutter_sizes.top).fill(false);
    if (gutter_sizes.left) markings.left = new Array(gutter_sizes.left).fill(false);
    if (gutter_sizes.right) markings.right = new Array(gutter_sizes.right).fill(false);
    if (gutter_sizes.bottom) markings.bottom = new Array(gutter_sizes.bottom).fill(false);
    return markings;
  };

  // Get current markings from store or initialize
  const current_markings = computed(() => progress_store.gutter_markings?.[puzzle_type] || initialize_markings());

  // toggle marking for specific gutter cell
  const toggle_gutter_marking = async (gutter_type: keyof GutterMarkings, index: number) => {
    const markings = { ...current_markings.value };
    if (!markings[gutter_type]) markings[gutter_type] = new Array(gutter_sizes[gutter_type]).fill(false);
    markings[gutter_type]![index] = !markings[gutter_type]![index];
    await progress_store.update_gutter_markings(puzzle_type, markings);
  };

  // get marking state for specific gutter cell
  const is_marked = (gutter_type: keyof GutterMarkings, index: number): boolean => {
    return current_markings.value[gutter_type]?.[index] || false;
  };

  // get css classes for gutter cell based on marking state
  const get_gutter_classes = (gutter_type: keyof GutterMarkings, index: number): string => {
    const base_classes = "cursor-pointer";
    const marked = is_marked(gutter_type, index);
    const opacity_class = marked ? "opacity-30" : "opacity-100";
    return `${base_classes} ${opacity_class}`;
  };

  // reset all markings for this puzzle
  const reset_markings = async () => await progress_store.reset_gutter_markings(puzzle_type);

  return {
    current_markings,
    toggle_gutter_marking,
    is_marked,
    get_gutter_classes,
    reset_markings
  };
}

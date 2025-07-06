// frontend/src/features/experiments/core/useExperimentPoints.ts

import { computed, ref } from "vue";
import { useGameScoring } from "./useGameScoring";
import type { PuzzleDefinition } from "@/services/game/engines/types";

export function useExperimentPoints() {
  const { calculateScore } = useGameScoring();

  // Points state that persists across experiment steps
  const points = ref<{ step_id: string; points: number }[]>([]);
  const total_points = computed(() => points.value.reduce((sum, entry) => sum + entry.points, 0));

  /**
   * Calculate and store points for current step
   */
  function recordStepPoints(step_id: string, currentBoard: number[][], definition: PuzzleDefinition): number {
    const stepPoints = calculateScore(currentBoard, definition);

    // Update or add points for this step
    const existingIndex = points.value.findIndex((p) => p.step_id === step_id);
    if (existingIndex >= 0) {
      points.value[existingIndex].points = stepPoints;
    } else {
      points.value.push({ step_id, points: stepPoints });
    }

    console.log(`Step ${step_id}: ${stepPoints} points (Total: ${total_points.value})`);
    return stepPoints;
  }

  /**
   * Get points for a specific step
   */
  function getStepPoints(step_id: string): number {
    return points.value.find((p) => p.step_id === step_id)?.points || 0;
  }

  /**
   * Reset all points (for testing)
   */
  function resetPoints() {
    points.value = [];
  }

  /**
   * Get breakdown of all points
   */
  function getPointsBreakdown() {
    return {
      total: total_points.value,
      steps: [...points.value],
      average: points.value.length > 0 ? total_points.value / points.value.length : 0,
    };
  }

  return {
    // State
    total_points,
    points: computed(() => points.value),

    // Methods
    recordStepPoints,
    getStepPoints,
    resetPoints,
    getPointsBreakdown,
  };
}

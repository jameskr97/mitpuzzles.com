<script setup lang="ts">
import { VIOLATION_MAP } from "@/features/games/violations.ts";
import Container from "@/components/ui/Container.vue";
import type { RuleViolation } from "@/services/game/engines/PuzzleEngine.ts";

defineProps({
  violations: { type: Array<RuleViolation>, required: false, default: [] },
});

function getMetadata(violation: RuleViolation) {
  // Replace 'type' with the actual property name that matches VIOLATION_MAP keys
  return VIOLATION_MAP[violation.rule_name] || { title: "Unknown Rule Violated", description: violation.rule_name };
}
</script>

<template>
  <Container>
    <div class="text-xl">Rule Violations</div>
    <div class="divider m-0"></div>
    <div class="flex flex-col gap-2">
      <div v-for="v in violations" :key="v.rule_name" class="text-sm">
        <div class="flex items-center gap-2">
          <span class="text-red-500">Violation:</span>
          <span>{{ getMetadata(v).title }}</span>
        </div>
        <div class="ml-2 text-gray-500">
          <span>{{ getMetadata(v).description }}</span>
          <div class="grid grid-cols-3">
            <div v-for="position in v.locations">
              <span>({{ position.row }}, {{ position.col }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="violations.length === 0">No Violations.</div>
  </Container>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { graph_node } from "@/features/experiment-core/graph/types";
import Container from "@/components/ui/Container.vue";
import { Button } from "@/components/ui/button";

// use content from config or fallback to default
const consent_content = `
  <h3>We need your consent to proceed</h3>
  <p>By completing this study, you are participating in a study being performed by
  cognitive scientists in the MIT Department of Brain and Cognitive Science.
  The purpose of this research is to understand how people reason and solve problems.</p>
  <p>You must be at least 18 years old to participate. There are neither specific benefits nor
  anticipated risks associated with participation in this study. Your participation in this
  study is completely voluntary, and you can withdraw at any time by simply exiting the study.
  You may decline to answer any or all of the following questions. Choosing not to participate
  or withdrawing will result in no penalty. Your anonymity is assured; the researchers who have
  requested your participation will not receive any personal information about you, and any
  information you provide will not be shared in association with any personally identifying information.</p>
  <p>If you have questions about this research, please contact the researchers by sending an email to
  <a href="mailto:support@mitpuzzles.com">support@mitpuzzles.com</a>. These researchers will do their best to communicate with you in a timely,
  professional, and courteous manner. If you have questions regarding your rights as a research subject,
  or if problems arise which you do not feel you can discuss with the researchers, please contact the
  MIT Institutional Review Board.</p>
  <p>Your participation in this research is voluntary.
  You may discontinue participation at any time during the research activity.
  You may print a copy of this consent form for your records.</p>
`;

defineProps<{ node: graph_node }>();
const emit = defineEmits(["complete"]);
</script>

<template>
  <div class="w-full flex-1 flex flex-col my-2 gap-5">
    <Container class="max-w-prose mx-auto">
      <div class="mx-auto prose flex-1" v-html="consent_content"></div>
    </Container>
    <Button variant="blue" @click="$emit('complete')" class="mx-auto max-w-prose"> I Consent </Button>
  </div>
</template>

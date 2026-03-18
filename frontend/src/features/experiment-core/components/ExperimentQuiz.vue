<script setup lang="ts">
import { type PropType, ref } from "vue";
import { Checkbox } from "@/core/components/ui/checkbox";
import { Button } from "@/core/components/ui/button";
import { Alert, AlertTitle } from "@/core/components/ui/alert";
import { shuffle } from "@/utils.ts";

interface QuizQuestion {
  question: string;
  answer: boolean;
}

// Define props
const props = defineProps({
  questions: {
    type: Array as PropType<QuizQuestion[]>,
    required: true,
  },
});
// then you would have to show
// Define emits
const shuffled_questions = shuffle(props.questions);
const emit = defineEmits(["onCorrect", "onIncorrect"]);
const userAnswers = ref<Record<number, boolean>>({});
props.questions.forEach((_, i) => (userAnswers.value[i] = false));

const showQuizWarning = ref(false);

function onQuizSubmitted() {
  const anyIncorrect = shuffled_questions.some((q, i) => userAnswers.value[i] !== q.answer);
  if (anyIncorrect) {
    emit("onIncorrect");
    showQuizWarning.value = true;
  } else {
    emit("onCorrect");
  }
}
</script>

<template>
  <div>
    <p class="mb-2">
      Please answer these brief comprehension questions before beginning the experiment. Check which of the following
      statements about the game are <span class="font-bold">true</span>:
    </p>
    <Alert v-if="showQuizWarning" variant="warning">
      <AlertTitle>Please double check your answers</AlertTitle>
    </Alert>
    <div class="flex flex-col space-y-1">
      <div v-for="(item, index) in questions" :key="`question-${index}`" class="flex items-start">
        <label class="flex items-center gap-2 cursor-pointer">
          <Checkbox v-model="userAnswers[index]" class=""></Checkbox>
          <span class="leading-relaxed select-none">{{ item.question }}</span>
        </label>
      </div>
      <Button class="mt-3 mx-auto" @click="onQuizSubmitted">Submit Quiz</Button>
    </div>
  </div>
</template>

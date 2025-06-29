<script setup lang="ts">
import { ref, type PropType } from "vue";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";

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

// Define emits
const emit = defineEmits(["evalResult"]);
const userAnswers = ref<Record<number, boolean>>({});
props.questions.forEach((_, i) => (userAnswers.value[i] = false));

const check_user_answers = () => {
  const anyIncorrect = props.questions?.some((q, i) => userAnswers.value[i] !== q.answer);
  const allCorrect = !anyIncorrect;
  emit("evalResult", allCorrect);
  return allCorrect;
};
</script>

<template>
  <div class="my-5">
    <h3 class="text-lg font-medium mb-4">Quiz</h3>
    <div class="flex flex-col space-y-3">
      <div v-for="(item, index) in questions" :key="`question-${index}`" class="flex items-start">
        <label class="flex items-center gap-2 cursor-pointer">
          <Checkbox v-model="userAnswers[index]" class=""></Checkbox>
          <span class="leading-relaxed select-none">{{ item.question }}</span>
        </label>
      </div>
      <Button class=" mt-3 mx-auto" @click="check_user_answers">Submit Quiz</Button>
    </div>
  </div>
</template>

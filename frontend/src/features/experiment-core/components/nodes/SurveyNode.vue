<script setup lang="ts">
import type { Ref } from "vue";
import { computed, inject, ref } from "vue";
import type { graph_node } from "@/features/experiment-core/graph/types";
import type { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import type { survey_meta, survey_question, survey_response_data } from "@/features/experiment-core/survey/types";
import { DEFAULT_SURVEY_QUESTIONS } from "@/features/experiment-core/survey/defaults";
import Container from "@/components/ui/Container.vue";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";

const props = defineProps<{ node: graph_node }>();
const emit = defineEmits(["complete"]);

const executor = inject<Ref<GraphExecutor>>("experiment-executor");
const survey_config = computed((): survey_meta => props.node.config?.meta || { questions: [] });

// combine default and custom questions
const all_questions = computed((): survey_question[][] => {
  const questions: survey_question[][] = [];

  // add defaults with deep copy to avoid mutation
  if (survey_config.value.include_defaults !== false) {
    DEFAULT_SURVEY_QUESTIONS.forEach((group) => {
      questions.push([...group]); // create a copy of each group
    });
  }

  // merge or append custom questions
  if (survey_config.value.questions) {
    survey_config.value.questions.forEach((group, index) => {
      if (questions[index]) {
        questions[index].push(...group); // merge into existing group
      } else {
        questions.push([...group]); // create new group with copy
      }
    });
  }

  return questions;
});
const responses = ref<survey_response_data>({});

// helper functions for multiple choice and other options
function handle_multiple_choice_change(
  question_id: string,
  option_value: string,
  checked: boolean,
  max_selections: number = 1,
) {
  if (!responses.value[question_id]) {
    responses.value[question_id] = [];
  }
  const current_selections = responses.value[question_id];

  if (checked) {
    // add selection if under max limit
    if (current_selections.length < max_selections) {
      responses.value[question_id] = [...current_selections, option_value];
    }
  } else {
    // remove selection
    responses.value[question_id] = current_selections.filter((val: string) => val !== option_value);
  }
}

function is_multiple_choice_selected(question_id: string, option_value: string): boolean {
  const selections = responses.value[question_id] || [];
  return selections.includes(option_value);
}

function can_select_more(question_id: string, max_selections: number = 1): boolean {
  const current_selections = responses.value[question_id] || [];
  return current_selections.length < max_selections;
}

function handle_other_text_change(question_id: string, text: string) {
  responses.value[`${question_id}_other`] = text;
}

function submit_survey() {
  if (executor?.value) {
    const current_node = executor.value.current_node;
    executor.value.data_collection.record_survey_responses(current_node.id, responses.value);
  }
  emit("complete");
}
</script>

<template>
  <template class="w-full flex-1 flex flex-col">
    <form class="flex flex-col gap-3 mx-auto prose flex-1 max-w-prose" @submit.prevent="submit_survey">
      <Container>
        <div class="text-3xl text-center">Completion Survey</div>
        <div class="text-lg pt-2 text-center">
          Thank you for completing our experiments. Please complete the following survey to be redirected back towards
          prolific.
        </div>
      </Container>

      <!-- root-grid -->
      <Container v-for="(question_group, i) in all_questions" class="grid grid-cols-[1.3fr_2fr] gap-3 items-center p-5">
        <template v-for="(question, index) in question_group" :key="question.id">
          <template v-if="question.type === 'number'">
            <div class="text-xl">{{ question.text }}</div>
            <Input
              type="number"
              v-model="responses[question.id]"
              :placeholder="question.placeholder"
              class="input w-full"
              :min="question.min"
              :max="question.max"
              required
            />
          </template>

          <template v-else-if="question.type === 'text'">
            <div class="text-xl">{{ question.text }}</div>
            <Input
              type="text"
              v-model="responses[question.id]"
              :placeholder="question.placeholder"
              class="input w-full"
              :required="question.required"
            />
          </template>

          <template v-else-if="question.type === 'dropdown'">
            <div class="text-xl">{{ question.text }}</div>
            <div class="flex flex-col gap-2">
              <Select :required="question.required" v-model="responses[question.id]">
                <SelectTrigger class="w-full">
                  <SelectValue :placeholder="question.placeholder" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem v-for="(item, i) in question.options" :value="item.value">
                      {{ item.label }}
                    </SelectItem>
                    <SelectItem v-if="question.other_option" value="other">
                      {{ question.other_option.label }}
                    </SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
              <!-- other text input for dropdown -->
              <Input
                v-if="question.other_option?.has_input && responses[question.id] === 'other'"
                type="text"
                placeholder="Please specify..."
                @input="(e) => handle_other_text_change(question.id, (e.target as HTMLInputElement).value)"
                class="mt-2"
              />
            </div>
          </template>

          <div v-else-if="question.type === 'multiple_choice'" class="col-span-2">
            <div class="text-xl">{{ question.text }}</div>
            <div class="flex flex-col gap-2">
              <div v-if="question.max_selections && question.max_selections > 1" class="text-sm text-gray-600">
                Select up to {{ question.max_selections }} options
              </div>
              <div v-for="(option, i) in question.options" :key="option.value" class="flex items-center space-x-2">
                <Checkbox
                  :id="`${question.id}_${option.value}`"
                  :checked="is_multiple_choice_selected(question.id, option.value)"
                  :disabled="
                    !is_multiple_choice_selected(question.id, option.value) &&
                    !can_select_more(question.id, question.max_selections || 1)
                  "
                  @update:model-value="
                    (checked) =>
                      handle_multiple_choice_change(question.id, option.value, checked, question.max_selections || 1)
                  "
                />
                <label
                  :for="`${question.id}_${option.value}`"
                  class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {{ option.label }}
                </label>
              </div>
              <!-- other option for multiple choice -->
              <div v-if="question.other_option" class="flex items-center space-x-2">
                <Checkbox
                  :id="`${question.id}_other`"
                  :checked="is_multiple_choice_selected(question.id, 'other')"
                  :disabled="
                    !is_multiple_choice_selected(question.id, 'other') &&
                    !can_select_more(question.id, question.max_selections || 1)
                  "
                  @update:model-value="
                    (checked) =>
                      handle_multiple_choice_change(question.id, 'other', checked, question.max_selections || 1)
                  "
                />
                <label
                  :for="`${question.id}_other`"
                  class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {{ question.other_option.label || "Other" }}
                </label>
              </div>
              <!-- other text input for multiple choice -->
              <Input
                v-if="question.other_option?.has_input && is_multiple_choice_selected(question.id, 'other')"
                type="text"
                placeholder="please specify..."
                @input="(e) => handle_other_text_change(question.id, (e.target as HTMLInputElement).value)"
                class="ml-6 mt-1"
              />
            </div>
          </div>

          <div v-else-if="question.type === 'textarea'" class="col-span-2">
            <div class="text-xl mb-2">{{ question.text }}</div>
            <div class="text-sm mb-2">{{ question.description }}</div>
            <Textarea
              v-model="responses[question.id]"
              :placeholder="question.placeholder || 'Your feedback about the experiment'"
              class="textarea w-full resize-vertical min-h-24"
              :rows="question.rows || 4"
              required
            ></Textarea>
          </div>

          <div v-else class="col-span-2 border border-red-500 bg-red-100 flex flex-col m-5">
            <div class="font-bold">Unknown Question Type</div>
            <div>{{ question }}</div>
          </div>
        </template>
      </Container>
      <Button variant="blue" type="submit" class="btn btn-primary mt-4 block mx-auto"> Submit </Button>
    </form>
  </template>
</template>

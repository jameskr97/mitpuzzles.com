<script setup lang="ts">
import { ref } from "vue";
import { submitExperimentSurvey } from "@/services/app.ts";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import Container from "@/components/ui/Container.vue";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useExperimentController } from "@/features/prolific.composables/useExperimentController.ts";

const age = ref<number | null>(null);
const gender = ref<string>("");
const education = ref<string>("");
const experience = ref<string>("");
const feedback = ref<string>("");

async function onSubmit() {
  const exp = useExperimentController("2025.05.29.sudoku");
  const surveyData = {
    age: age.value,
    gender: gender.value,
    education: education.value,
    experience: experience.value,
    feedback: feedback.value,
  };
  console.log(exp)
  try {
    if (!exp.experiment_state.value?.participation_id) return;
    const res = await submitExperimentSurvey(exp.experiment_state.value?.participation_id, surveyData);
    const completion_code = res.data.completion_code;
    window.location.href = `https://app.prolific.co/submissions/complete?cc=${completion_code}`;
  } catch (huh) {
    console.error("Error submitting survey:", huh);
  }
}
</script>

<template>
  <div class="w-full flex-1 flex flex-col">
    <form class="flex flex-col gap-3 mx-auto prose flex-1 max-w-prose" @submit.prevent="onSubmit">
      <Container>
        <div class="text-3xl text-center">Completion Survey</div>
        <div class="text-lg pt-2 text-center">
          Thank you for completing our experiments. Please submit out the following survey to be redirected back towards
          prolific.
        </div>
        <div class="text-sm italic mt-2 text-center">
          Did you enjoy playing? Check out <a href="https://mitpuzzles.com">mitpuzzles.com</a> for more puzzles!
        </div>
      </Container>
      <Container class="grid grid-cols-[1.3fr_2fr] gap-3 items-center p-5">
        <!-- Age -->
        <div class="text-xl">Age</div>
        <Input v-model="age" type="number" placeholder="Age" class="input w-full" min="18" max="130" required />

        <!-- Gender -->
        <div class="text-xl">Gender</div>
        <Select v-model="gender" required>
          <SelectTrigger class="w-full">
            <SelectValue placeholder="Gender" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="other">Other</SelectItem>
              <SelectItem value="none">Prefer not to say</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <!--        <select v-model="gender" class="select w-full" required>-->
        <!--          <option disabled selected>Select...</option>-->

        <!--        </select>-->

        <div class="text-xl">Education Level</div>
        <Select v-model="education" required>
          <SelectTrigger class="w-full">
            <SelectValue placeholder="Education Level" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="high_school">High School</SelectItem>
              <SelectItem value="bachelors">Bachelor's Degree</SelectItem>
              <SelectItem value="masters">Master's Degree</SelectItem>
              <SelectItem value="doctorate">Doctorate</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>

        <div class="text-xl text-nowrap">Prior Sudoku Experience</div>
        <Select v-model="experience" required>
          <SelectTrigger class="w-full">
            <SelectValue placeholder="Prior Sudoku Experience" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="0">0 prior games</SelectItem>
              <SelectItem value="1-5">1-5 prior games</SelectItem>
              <SelectItem value="5-50">5-50 prior games</SelectItem>
              <SelectItem value="more-50">More than 50 prior games</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </Container>

      <Container>
        <div class="text-xl mb-2">General Feedback</div>
        <div class="text-base mb-2">
          Did you experience any issues, or do you have any other feedback you would like to share with the researchers?
        </div>
        <Textarea
          v-model="feedback"
          placeholder="Your feedback about the experiment"
          class="textarea w-full"
          rows="4"
        ></Textarea>
      </Container>

      <Button class="btn btn-primary mt-4 block mx-auto">Submit</Button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { submitExperimentSurvey } from "@/services/app.ts";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";

const age = ref<number | null>(null);
const gender = ref<string>('');
const education = ref<string>('');
const experience = ref<string>('');
const feedback = ref<string>('');

async function onSubmit() {
  const exp = useCurrentExperiment()
  const surveyData = {
    age: age.value,
    gender: gender.value,
    education: education.value,
    experience: experience.value,
    feedback: feedback.value
  };
  try {
    if (!exp.prolific_session_id) return;
    const res = await submitExperimentSurvey(exp.prolific_session_id, surveyData);
    const completion_code = res.data.completion_code;
    window.location.href = `https://app.prolific.co/submissions/complete?cc=${completion_code}`;
  } catch (huh) {
    console.error('Error submitting survey:', huh);
  }
}
</script>

<template>
  <div class="w-full flex-1 flex flex-col">
    <form class="mx-auto prose flex-1 max-w-prose" @submit.prevent="onSubmit">
      <div class="text-3xl text-center">Completion Survey</div>
      <div class="divider"></div>
      <div class="text-lg pt-2 text-center">
        Thank you for completing our experiments. Please submit out the following survey to be redirected back towards
        prolific.
      </div>
      <div class="grid grid-cols-[1.3fr_2fr] mt-2 gap-2 items-center">
        <!-- Age -->
        <div class="text-xl">Age</div>
        <input
          v-model.number="age"
          type="number"
          placeholder="Age"
          class="input w-full"
          max="130"
          required
        />

        <!-- Gender -->
        <div class="text-xl">Gender</div>
        <select v-model="gender" class="select w-full" required>
          <option disabled selected>Select...</option>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
          <option value="none">Prefer not to say</option>
        </select>

        <div class="text-xl">Education Level</div>
        <select v-model="education" class="select w-full" name="education" required>
          <option disabled selected>Select...</option>
          <option value="high_school">High School</option>
          <option value="bachelors">Bachelor's Degree</option>
          <option value="masters">Master's Degree</option>
          <option value="doctorate">Doctorate</option>
          <option value="other">Other</option>
        </select>

        <div class="text-xl">Prior Sudoku Experience</div>
        <select v-model="experience" class="select w-full" name="experience" required>
          <option disabled selected>Select...</option>
          <option value="0">0 prior games</option>
          <option value="1-5">1-5 prior games</option>
          <option value="5-50">5-50 prior games</option>
          <option value="more-50">More than 50 prior games</option>
        </select>
      </div>

      <div class="divider"></div>

      <div class="text-xl mb-2">General Feedback</div>
      <div class="text-base mb-2">Did you experience any issues, or do you have any other feedback you would like to share with the researchers?</div>
      <textarea
        v-model="feedback"
        placeholder="Your feedback about the experiment"
        class="textarea w-full"
        rows="4"
      ></textarea>

      <button type="submit" class="btn btn-primary mt-4 block mx-auto">Submit</button>
    </form>
  </div>
</template>

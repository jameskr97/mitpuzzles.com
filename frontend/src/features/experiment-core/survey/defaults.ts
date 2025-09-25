import type { survey_question } from "./types";

/** default demographic questions for research surveys */
export const DEFAULT_SURVEY_QUESTIONS: survey_question[][] = [
  [
    {
      id: "age",
      type: "number",
      text: "Age",
      placeholder: "Age",
      min: 18,
      max: 130,
      required: true,
    },
    {
      id: "gender",
      type: "dropdown",
      text: "Gender",
      placeholder: "Gender",
      options: [
        { value: "male", label: "Male" },
        { value: "female", label: "Female" },
        { value: "other", label: "Other" },
        { value: "none", label: "Prefer not to say" },
      ],
      required: true,
    },
    {
      id: "education",
      type: "dropdown",
      text: "Education Level",
      placeholder: "Education Level",
      options: [
        { value: "high_school", label: "High School" },
        { value: "bachelors", label: "Bachelor's Degree" },
        { value: "masters", label: "Master's Degree" },
        { value: "doctorate", label: "Doctorate" },
      ],
      other_option: { label: "Other", has_input: false },
      required: true,
    },
  ],
  [
    {
      id: "feedback",
      type: "textarea",
      text: "General Feedback",
      placeholder: "Your feedback about the experiment",
      description: `Please describe your experience with the experiment. Were the instructions easy to understand? Was there
              anything you liked or disliked? Did interaction with the game board work as you expect? Any suggestions
              for improvement?`,
      rows: 4,
      required: true,
    },
  ],
];

/** simplified survey question interface */
export interface survey_question {
  id: string; // required - used as key for storing responses
  type: "text" | "textarea" | "rating" | "multiple_choice" | "dropdown" | "number";
  text: string; // question text
  required?: boolean; // default true

  // type-specific config
  scale?: [number, number]; // for rating questions [min, max]
  options?: { value: string; label: string }[]; // for multiple choice/dropdown
  placeholder?: string; // for text inputs and dropdowns
  min?: number;
  max?: number; // for number inputs
  rows?: number; // for textarea
  description?: string; // for textarea
  max_selections?: number; // for multiple_choice questions - limits number of selections (default: 1)
  other_option?: { label: string; has_input: boolean }; // adds "other" option with optional text input
}

/** simplified survey configuration */
export interface survey_meta {
  questions: survey_question[][];
  include_defaults?: boolean; // add default demographic questions
}

/** survey response data structure */
export interface survey_response_data {
  [question_id: string]: any; // response value keyed by question id
}

/** complete survey data with metadata */
export interface survey_data {
  responses: survey_response_data;
  metadata: {
    timestamp: number;
    node_id: string;
    completion_time?: number; // time spent on survey
  };
}
